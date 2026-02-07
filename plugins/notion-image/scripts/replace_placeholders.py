#!/usr/bin/env python3
"""
replace_placeholders.py - Notionページ内のプレースホルダーを画像に置換

使用法:
  python replace_placeholders.py <markdown_file> <page_id> [--dry-run]
"""

import os
import sys
import re
import argparse
import requests
from pathlib import Path


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


def get_all_blocks(page_id, headers):
    """ページの全ブロックを取得"""
    blocks = []
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} {resp.text}", file=sys.stderr)
            return blocks
        data = resp.json()
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
    for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', md_file.read_text()):
        alt, path = match.groups()
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
    resp = requests.post("https://api.notion.com/v1/file_uploads",
                        headers=headers, json={"name": filename, "content_type": content_type})
    if resp.status_code != 200:
        return None
    upload_obj = resp.json()

    # Step 2: Send file
    with open(file_path, "rb") as f:
        resp = requests.post(upload_obj["upload_url"],
                            headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"},
                            files={"file": (filename, f, content_type)})
    if resp.status_code != 200:
        return None

    return upload_obj["id"]


def delete_block(block_id, headers):
    """ブロックを削除"""
    resp = requests.delete(f"https://api.notion.com/v1/blocks/{block_id}", headers=headers)
    return resp.status_code == 200


def insert_image(page_id, upload_id, after_id, headers, caption=None):
    """画像ブロックを挿入"""
    image_block = {"type": "image", "image": {"type": "file_upload", "file_upload": {"id": upload_id}}}
    if caption:
        image_block["image"]["caption"] = [{"type": "text", "text": {"content": caption}}]
    payload = {"children": [image_block]}
    if after_id:
        payload["after"] = after_id
    resp = requests.patch(f"https://api.notion.com/v1/blocks/{page_id}/children", headers=headers, json=payload)
    return resp.status_code == 200


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
