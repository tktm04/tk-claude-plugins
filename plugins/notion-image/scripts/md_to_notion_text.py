#!/usr/bin/env python3
"""
md_to_notion_text.py - Markdownをプレースホルダー付きで変換

使用法:
  python md_to_notion_text.py <markdown_file> [--no-placeholder]

出力: 変換後のMarkdown（画像はプレースホルダーに置換）

注意: このスクリプトは変換のみ。Notionへのアップロードは
      Claude Codeが Notion MCP を使って行う。
"""

import re
import sys
from pathlib import Path


# Notionが受け付ける絶対リンクの代表的なスキーム
ABSOLUTE_URL_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "ftp://",
)


def is_relative_link(target: str) -> bool:
    """Return True if the Markdown link target should be treated as relative."""
    if not target:
        return True
    cleaned = target.strip()
    if not cleaned:
        return True
    lowered = cleaned.lower()
    if cleaned.startswith("//"):
        return False
    if any(lowered.startswith(prefix) for prefix in ABSOLUTE_URL_PREFIXES):
        return False
    # Anything without a scheme (e.g. proposal.md, ../foo/bar) is treated as relative
    return "://" not in cleaned


def strip_relative_links(content: str) -> str:
    """Replace relative Markdown links with their link text only."""

    def replace_link(match: re.Match) -> str:
        text = match.group(1)
        target = match.group(2)
        return text if is_relative_link(target) else match.group(0)

    # 非貪欲にマッチし、ネストしたリンクは想定しない
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    return link_pattern.sub(replace_link, content)


def convert_markdown(md_path: str, use_placeholder: bool = True) -> str:
    """Markdownを変換し、画像参照をプレースホルダーに置換"""
    md_file = Path(md_path)
    try:
        content = md_file.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error: Failed to read file: {e}", file=sys.stderr)
        sys.exit(1)

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

    # 相対リンク([text](path/to/file))はリンクテキストだけ残す
    content = strip_relative_links(content)

    return content


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert Markdown for Notion upload')
    parser.add_argument('markdown_file', help='Path to the Markdown file')
    parser.add_argument('--no-placeholder', action='store_true',
                        help='Remove image references instead of inserting placeholders (default: insert placeholders)')

    args = parser.parse_args()

    if not Path(args.markdown_file).exists():
        print(f"Error: File not found: {args.markdown_file}", file=sys.stderr)
        sys.exit(1)

    use_placeholder = not args.no_placeholder
    converted = convert_markdown(args.markdown_file, use_placeholder)
    print(converted)


if __name__ == "__main__":
    main()
