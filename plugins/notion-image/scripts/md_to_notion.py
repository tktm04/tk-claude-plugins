#!/usr/bin/env python3
"""
md_to_notion.py - MarkdownファイルをNotionページにアップロード（テキスト＋画像）

使用法:
  python md_to_notion.py <markdown_file> <page_id> [options]

Options:
  --dry-run    アップロードせず確認のみ
  --append     既存コンテンツに追記（デフォルトは置換）

依存関係: 標準ライブラリのみ（Python 3.9+）
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import uuid


def load_notion_token():
    """NOTION_TOKEN を読み込む"""
    config_path = Path.home() / ".config/notion-image/.env"
    if config_path.exists():
        for line in config_path.read_text().splitlines():
            if line.startswith("NOTION_TOKEN="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")


def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }


def http_request(url, method="GET", headers=None, data=None, timeout=30):
    """標準ライブラリでHTTPリクエストを実行"""
    headers = headers or {}
    req = Request(url, method=method)
    for key, value in headers.items():
        req.add_header(key, value)

    body = None
    if data is not None:
        if isinstance(data, dict):
            body = json.dumps(data).encode('utf-8')
            req.add_header("Content-Type", "application/json")
        elif isinstance(data, bytes):
            body = data

    try:
        with urlopen(req, data=body, timeout=timeout) as resp:
            return resp.status, resp.read().decode('utf-8')
    except HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except URLError as e:
        print(f"Error: Request failed: {e}", file=sys.stderr)
        return None, None


def create_multipart_body(filename, file_data, content_type):
    """multipart/form-data ボディを手動で構築"""
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"

    body = []
    body.append(f"--{boundary}".encode())
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
    body.append(f"Content-Type: {content_type}".encode())
    body.append(b"")
    body.append(file_data)
    body.append(f"--{boundary}--".encode())
    body.append(b"")

    return b"\r\n".join(body), boundary


def upload_file_multipart(url, token, filename, file_data, content_type, timeout=60):
    """multipart/form-data でファイルをアップロード"""
    body, boundary = create_multipart_body(filename, file_data, content_type)

    req = Request(url, method="POST", data=body)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", "2022-06-28")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode('utf-8')
    except HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except URLError as e:
        print(f"Error: Upload failed: {e}", file=sys.stderr)
        return None, None


# =============================================================================
# Markdown → Notion ブロック変換
# =============================================================================

def create_rich_text(text):
    """テキストをリッチテキストオブジェクトに変換"""
    if not text:
        return []

    # インラインコード、太字、斜体、リンクを処理
    result = []
    remaining = text

    while remaining:
        # インラインコード `code`
        match = re.search(r'`([^`]+)`', remaining)
        if match:
            before = remaining[:match.start()]
            if before:
                result.extend(parse_inline_formatting(before))
            result.append({
                "type": "text",
                "text": {"content": match.group(1)},
                "annotations": {"code": True}
            })
            remaining = remaining[match.end():]
            continue

        # それ以外
        result.extend(parse_inline_formatting(remaining))
        break

    return result if result else [{"type": "text", "text": {"content": text}}]


def parse_inline_formatting(text):
    """太字、斜体、リンクを処理"""
    result = []
    remaining = text

    while remaining:
        # リンク [text](url)
        match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', remaining)
        if match:
            before = remaining[:match.start()]
            if before:
                result.append({"type": "text", "text": {"content": before}})
            result.append({
                "type": "text",
                "text": {"content": match.group(1), "link": {"url": match.group(2)}}
            })
            remaining = remaining[match.end():]
            continue

        # 太字 **text**
        match = re.search(r'\*\*([^*]+)\*\*', remaining)
        if match:
            before = remaining[:match.start()]
            if before:
                result.append({"type": "text", "text": {"content": before}})
            result.append({
                "type": "text",
                "text": {"content": match.group(1)},
                "annotations": {"bold": True}
            })
            remaining = remaining[match.end():]
            continue

        # 斜体 *text* or _text_
        match = re.search(r'(?<!\*)\*([^*]+)\*(?!\*)|_([^_]+)_', remaining)
        if match:
            before = remaining[:match.start()]
            if before:
                result.append({"type": "text", "text": {"content": before}})
            content = match.group(1) or match.group(2)
            result.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"italic": True}
            })
            remaining = remaining[match.end():]
            continue

        # マッチなし
        if remaining:
            result.append({"type": "text", "text": {"content": remaining}})
        break

    return result


def markdown_to_blocks(content, md_dir):
    """MarkdownをNotionブロックのリストに変換"""
    blocks = []
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # 空行
        if not line.strip():
            i += 1
            continue

        # コードブロック ```
        if line.strip().startswith('```'):
            language = line.strip()[3:].strip() or "plain text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # 閉じる ```
            blocks.append({
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": '\n'.join(code_lines)}}],
                    "language": language
                }
            })
            continue

        # 見出し
        heading_match = re.match(r'^(#{1,3})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            block_type = f"heading_{level}"
            blocks.append({
                "type": block_type,
                block_type: {"rich_text": create_rich_text(text)}
            })
            i += 1
            continue

        # 画像 ![alt](path) → プレースホルダー（後で置換）
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', line.strip())
        if img_match:
            alt, path = img_match.groups()
            if not path.startswith(('http://', 'https://')):
                # ローカル画像はプレースホルダー
                filename = Path(path).name
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"[画像: {filename}]"}}]},
                    "_image_placeholder": {"path": path, "alt": alt, "filename": filename}
                })
            else:
                # URL画像はそのまま埋め込み
                blocks.append({
                    "type": "image",
                    "image": {"type": "external", "external": {"url": path}}
                })
            i += 1
            continue

        # 引用 >
        if line.startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].startswith('>'):
                quote_lines.append(lines[i][1:].strip())
                i += 1
            blocks.append({
                "type": "quote",
                "quote": {"rich_text": create_rich_text(' '.join(quote_lines))}
            })
            continue

        # 番号付きリスト
        num_match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if num_match:
            blocks.append({
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": create_rich_text(num_match.group(2))}
            })
            i += 1
            continue

        # 箇条書きリスト
        bullet_match = re.match(r'^[-*+]\s+(.+)$', line)
        if bullet_match:
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": create_rich_text(bullet_match.group(1))}
            })
            i += 1
            continue

        # 水平線
        if re.match(r'^[-*_]{3,}\s*$', line):
            blocks.append({"type": "divider", "divider": {}})
            i += 1
            continue

        # 通常の段落
        para_lines = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,3}\s|[-*+]\s|\d+\.\s|>|```|!\[)', lines[i]):
            para_lines.append(lines[i])
            i += 1

        text = ' '.join(para_lines)
        # 段落内の画像参照をプレースホルダーに変換
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', lambda m: f"[画像: {Path(m.group(2)).name}]", text)

        blocks.append({
            "type": "paragraph",
            "paragraph": {"rich_text": create_rich_text(text)}
        })

    return blocks


# =============================================================================
# Notion API 操作
# =============================================================================

def get_all_blocks(page_id, headers):
    """ページの全ブロックを取得"""
    blocks = []
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    while url:
        status, body = http_request(url, headers=headers, timeout=30)
        if status is None or status != 200:
            if body:
                print(f"Error: {status} {body}", file=sys.stderr)
            return blocks
        data = json.loads(body)
        blocks.extend(data.get("results", []))
        if data.get("has_more"):
            url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100&start_cursor={data['next_cursor']}"
        else:
            url = None
    return blocks


def delete_all_blocks(page_id, headers):
    """ページの全ブロックを削除"""
    blocks = get_all_blocks(page_id, headers)
    for block in blocks:
        status, body = http_request(
            f"https://api.notion.com/v1/blocks/{block['id']}",
            method="DELETE",
            headers=headers,
            timeout=30
        )
        if status is not None and status != 200 and body:
            print(f"Warning: Failed to delete block: {status}", file=sys.stderr)
    return len(blocks)


def append_blocks(page_id, blocks, headers):
    """ブロックをページに追加（100件ずつ）"""
    # プレースホルダー情報を除去してAPIに送信
    api_blocks = []
    for block in blocks:
        b = {k: v for k, v in block.items() if not k.startswith('_')}
        api_blocks.append(b)

    # 100件ずつ分割
    for i in range(0, len(api_blocks), 100):
        chunk = api_blocks[i:i+100]
        status, body = http_request(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            method="PATCH",
            headers=headers,
            data={"children": chunk},
            timeout=60
        )
        if status is None or status != 200:
            if body:
                print(f"Error: Append blocks failed: {status} {body}", file=sys.stderr)
            return False
    return True


def upload_image(file_path, token, headers):
    """画像をアップロード"""
    filename = Path(file_path).name
    ext = Path(file_path).suffix.lower()
    content_type = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".gif": "image/gif", ".webp": "image/webp"}.get(ext, "image/png")

    # Step 1: Create upload
    status, body = http_request(
        "https://api.notion.com/v1/file_uploads",
        method="POST",
        headers=headers,
        data={"name": filename, "content_type": content_type},
        timeout=30
    )
    if status is None or status != 200:
        if body:
            print(f"Error: Create upload failed: {status} {body}", file=sys.stderr)
        return None
    upload_obj = json.loads(body)

    # Step 2: Send file
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
    except OSError as e:
        print(f"Error: Failed to read image: {e}", file=sys.stderr)
        return None

    status, resp_body = upload_file_multipart(
        upload_obj["upload_url"],
        token,
        filename,
        file_data,
        content_type,
        timeout=60
    )
    if status is None or status != 200:
        if resp_body:
            print(f"Error: File upload failed: {status} {resp_body}", file=sys.stderr)
        return None

    return upload_obj["id"]


def replace_placeholders(page_id, blocks, md_dir, token, headers):
    """プレースホルダーを実画像に置換"""
    # ページのブロックを取得
    page_blocks = get_all_blocks(page_id, headers)

    # プレースホルダーを探す
    placeholders = []
    for block in page_blocks:
        if block["type"] == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if rich_text:
                text = rich_text[0].get("plain_text", "")
                match = re.search(r'\[画像:\s*(.+?)\]', text)
                if match:
                    placeholders.append({
                        "block_id": block["id"],
                        "filename": match.group(1).strip()
                    })

    if not placeholders:
        return 0

    # 画像情報を収集
    images = {}
    for block in blocks:
        if "_image_placeholder" in block:
            info = block["_image_placeholder"]
            path = info["path"]
            if Path(path).is_absolute():
                img_path = Path(path)
            else:
                img_path = md_dir / path
            if img_path.exists():
                images[info["filename"]] = {
                    "path": str(img_path.resolve()),
                    "caption": info.get("alt")
                }

    # 置換処理
    success = 0
    for p in placeholders:
        filename = p["filename"]
        block_id = p["block_id"]

        if filename not in images:
            continue

        img = images[filename]
        upload_id = upload_image(img["path"], token, headers)
        if not upload_id:
            print(f"  {filename}: FAIL (upload)", file=sys.stderr)
            continue

        # 前のブロックIDを取得
        prev_id = None
        for j, b in enumerate(page_blocks):
            if b["id"] == block_id and j > 0:
                prev_id = page_blocks[j-1]["id"]
                break

        # プレースホルダー削除
        status, _ = http_request(
            f"https://api.notion.com/v1/blocks/{block_id}",
            method="DELETE",
            headers=headers,
            timeout=30
        )
        if status != 200:
            print(f"  {filename}: FAIL (delete)", file=sys.stderr)
            continue

        # 画像挿入
        image_block = {"type": "image", "image": {"type": "file_upload", "file_upload": {"id": upload_id}}}
        if img.get("caption"):
            image_block["image"]["caption"] = [{"type": "text", "text": {"content": img["caption"]}}]

        payload = {"children": [image_block]}
        if prev_id:
            payload["after"] = prev_id

        status, _ = http_request(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            method="PATCH",
            headers=headers,
            data=payload,
            timeout=30
        )
        if status == 200:
            print(f"  {filename}: OK")
            success += 1
        else:
            print(f"  {filename}: FAIL (insert)", file=sys.stderr)

    return success


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Upload Markdown to Notion page')
    parser.add_argument('markdown_file', help='Path to the Markdown file')
    parser.add_argument('page_id', help='Notion page ID')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be uploaded')
    parser.add_argument('--append', action='store_true', help='Append to existing content (default: replace)')
    args = parser.parse_args()

    # トークン読み込み
    token = load_notion_token()
    if not token:
        print("Error: NOTION_TOKEN not found", file=sys.stderr)
        print("Set it in ~/.config/notion-image/.env or as environment variable", file=sys.stderr)
        sys.exit(1)

    headers = get_headers(token)
    md_file = Path(args.markdown_file)
    md_dir = md_file.parent

    # Markdown読み込み
    if not md_file.exists():
        print(f"Error: File not found: {args.markdown_file}", file=sys.stderr)
        sys.exit(1)

    try:
        content = md_file.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error: Failed to read file: {e}", file=sys.stderr)
        sys.exit(1)

    # ブロックに変換
    blocks = markdown_to_blocks(content, md_dir)

    # 画像プレースホルダーをカウント
    image_count = sum(1 for b in blocks if "_image_placeholder" in b)

    print(f"Parsed: {len(blocks)} blocks, {image_count} images")

    if args.dry_run:
        print("\n[Dry run] Would upload:")
        for i, block in enumerate(blocks):
            block_type = block["type"]
            if "_image_placeholder" in block:
                info = block["_image_placeholder"]
                print(f"  [{i+1}] {block_type} (image: {info['filename']})")
            else:
                print(f"  [{i+1}] {block_type}")
        return

    # 既存コンテンツを削除（appendモードでない場合）
    if not args.append:
        print("Clearing existing content...")
        deleted = delete_all_blocks(args.page_id, headers)
        print(f"  Deleted {deleted} blocks")

    # ブロックを追加
    print("Uploading text content...")
    if not append_blocks(args.page_id, blocks, headers):
        print("Error: Failed to upload content", file=sys.stderr)
        sys.exit(1)
    print("  Done")

    # 画像を置換
    if image_count > 0:
        print(f"Uploading {image_count} images...")
        success = replace_placeholders(args.page_id, blocks, md_dir, token, headers)
        print(f"  Done: {success}/{image_count} images")

    print("\nUpload complete!")


if __name__ == "__main__":
    main()
