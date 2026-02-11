#!/usr/bin/env python3
"""
replace_placeholders.py - Notionページ内のプレースホルダーを画像に置換

使用法:
  python replace_placeholders.py <markdown_file> <page_id> [--dry-run]

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


def find_placeholders(blocks):
    """プレースホルダーブロックを探す"""
    placeholders = []
    for block in blocks:
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
    return placeholders


def extract_images(md_path):
    """Markdownから画像情報を抽出"""
    md_file = Path(md_path)
    md_dir = md_file.parent
    images = {}
    try:
        content = md_file.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error: Failed to read file: {e}", file=sys.stderr)
        return images

    for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', content):
        alt, path = match.groups()

        # URL画像はスキップ
        if path.startswith(('http://', 'https://')):
            continue

        # 絶対パス/相対パスを適切に処理
        if Path(path).is_absolute():
            img_path = Path(path)
        else:
            img_path = md_dir / path

        if img_path.exists():
            images[img_path.name] = {"path": str(img_path.resolve()), "caption": alt or None}
    return images


def upload_image(file_path, token, headers):
    """画像をアップロード（3ステップ）"""
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


def delete_block(block_id, headers):
    """ブロックを削除"""
    status, body = http_request(
        f"https://api.notion.com/v1/blocks/{block_id}",
        method="DELETE",
        headers=headers,
        timeout=30
    )
    if status is not None and status != 200 and body:
        print(f"Error: Delete block failed: {status} {body}", file=sys.stderr)
    return status == 200


def insert_image(page_id, upload_id, after_id, headers, caption=None):
    """画像ブロックを挿入"""
    image_block = {"type": "image", "image": {"type": "file_upload", "file_upload": {"id": upload_id}}}
    if caption:
        image_block["image"]["caption"] = [{"type": "text", "text": {"content": caption}}]
    payload = {"children": [image_block]}
    if after_id:
        payload["after"] = after_id

    status, body = http_request(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        method="PATCH",
        headers=headers,
        data=payload,
        timeout=30
    )
    if status is not None and status != 200 and body:
        print(f"Error: Insert image failed: {status} {body}", file=sys.stderr)
    return status == 200


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_file')
    parser.add_argument('page_id')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    token = load_notion_token()
    if not token:
        print("Error: NOTION_TOKEN not found", file=sys.stderr)
        sys.exit(1)

    headers = get_headers(token)
    images = extract_images(args.markdown_file)
    blocks = get_all_blocks(args.page_id, headers)
    placeholders = find_placeholders(blocks)

    print(f"Found {len(placeholders)} placeholders, {len(images)} images")

    if args.dry_run:
        for p in placeholders:
            status = "OK" if p['filename'] in images else "NOT FOUND"
            print(f"  [{status}] {p['filename']}")
        return

    success = 0
    for i, p in enumerate(placeholders):
        filename, block_id = p['filename'], p['block_id']
        print(f"[{i+1}/{len(placeholders)}] {filename}", end=" ")

        if filename not in images:
            print("SKIP (not in markdown)")
            continue

        img = images[filename]
        upload_id = upload_image(img['path'], token, headers)
        if not upload_id:
            print("FAIL (upload)")
            continue

        # 前のブロックIDを取得
        prev_id = None
        for j, b in enumerate(blocks):
            if b["id"] == block_id and j > 0:
                prev_id = blocks[j-1]["id"]
                break

        if not delete_block(block_id, headers):
            print("FAIL (delete)")
            continue

        if insert_image(args.page_id, upload_id, prev_id, headers, img.get('caption')):
            print("OK")
            success += 1
        else:
            print("FAIL (insert)")

    print(f"\nDone: {success}/{len(placeholders)}")


if __name__ == "__main__":
    main()
