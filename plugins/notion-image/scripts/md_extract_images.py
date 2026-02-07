#!/usr/bin/env python3
"""
md_extract_images.py - Markdownから画像参照を抽出してJSON出力

使用法:
  python md_extract_images.py <markdown_file>

出力: JSON形式
  [
    {"path": "/abs/path/to/img.png", "caption": "Figure 1", "after_heading": "結果"},
    ...
  ]
"""

import re
import json
import sys
from pathlib import Path


def extract_images(md_path: str) -> list[dict]:
    """Markdownから画像参照を抽出し、直前の見出しも記録"""
    md_file = Path(md_path)
    md_dir = md_file.parent
    content = md_file.read_text()

    images = []
    current_heading = None

    for line in content.split('\n'):
        # 見出しを追跡
        if m := re.match(r'^(#{1,3})\s+(.+)$', line):
            current_heading = m.group(2).strip()

        # 画像参照を検出 ![alt](path)
        if m := re.search(r'!\[([^\]]*)\]\(([^)]+)\)', line):
            alt, path = m.groups()

            # 相対パスを絶対パスに変換
            img_path = md_dir / path
            if img_path.exists():
                images.append({
                    "path": str(img_path.resolve()),
                    "caption": alt or None,
                    "after_heading": current_heading
                })
            else:
                print(f"Warning: Image not found: {img_path}", file=sys.stderr)

    return images


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python md_extract_images.py <markdown_file>", file=sys.stderr)
        sys.exit(1)

    md_path = sys.argv[1]
    if not Path(md_path).exists():
        print(f"Error: File not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    images = extract_images(md_path)
    print(json.dumps(images, ensure_ascii=False, indent=2))
