#!/usr/bin/env python3
"""
md_to_notion_text.py - Markdownをプレースホルダー付きで変換

使用法:
  python md_to_notion_text.py <markdown_file> [--placeholder]

出力: 変換後のMarkdown（画像はプレースホルダーに置換）

注意: このスクリプトは変換のみ。Notionへのアップロードは
      Claude Codeが Notion MCP を使って行う。
"""

import re
import sys
from pathlib import Path


def convert_markdown(md_path: str, use_placeholder: bool = True) -> str:
    """Markdownを変換し、画像参照をプレースホルダーに置換"""
    md_file = Path(md_path)
    content = md_file.read_text()

    if use_placeholder:
        # ![alt](path) → [画像: filename]
        def replace_image(match):
            alt = match.group(1)
            path = match.group(2)
            filename = Path(path).name
            caption = alt if alt else filename
            return f"[画像: {filename}]"

        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image, content)
    else:
        # 画像行を削除
        content = re.sub(r'!\[[^\]]*\]\([^)]+\)\n?', '', content)

    return content


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert Markdown for Notion upload')
    parser.add_argument('markdown_file', help='Path to the Markdown file')
    parser.add_argument('--placeholder', action='store_true', default=True,
                        help='Insert placeholders for images (default: True)')
    parser.add_argument('--no-placeholder', action='store_true',
                        help='Remove image references instead of placeholders')

    args = parser.parse_args()

    if not Path(args.markdown_file).exists():
        print(f"Error: File not found: {args.markdown_file}", file=sys.stderr)
        sys.exit(1)

    use_placeholder = not args.no_placeholder
    converted = convert_markdown(args.markdown_file, use_placeholder)
    print(converted)


if __name__ == "__main__":
    main()
