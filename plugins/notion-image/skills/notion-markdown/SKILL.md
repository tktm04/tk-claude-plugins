---
name: notion-markdown
description: Markdownファイル（テキスト + 画像）をNotionページにアップロードする。使用場面: レポートやドキュメントをNotionに公開したい時。トリガー: md-to-notion, markdown notion, mdアップロード, notionに公開
allowed-tools: Bash(md-to-notion-text:*), Bash(md-to-notion-images:*), Read, mcp__notion__notion-update-page, mcp__notion__notion-fetch
---

# Markdown to Notion Upload

Markdownファイル（テキスト + 画像）をNotionページにアップロードするスキル。

## クイック判断フロー

```
MarkdownをNotionにアップロードしたい
         │
         ├── テキスト + 画像（推奨）
         │   └── このスキルのワークフローに従う
         │
         ├── テキストのみ
         │   └── md-to-notion-text → Notion MCP
         │
         └── 画像のみ
             └── md-to-notion-images（または /notion-image スキル）
```

## ワークフロー

### Step 1: Markdownをプレースホルダー付きで変換

```bash
python3 scripts/md_to_notion_text.py <markdown_file> --placeholder > /tmp/converted.md
```

出力例:
```markdown
# レポート

## 結果
[画像: result.png]

## 考察
...
```

### Step 2: Notion MCPでテキストをアップロード

```
notion-update-page を使用:
- page_id: 対象ページID
- content_format: markdown
- content: /tmp/converted.md の内容
- mode: replace_content
```

### Step 3: 画像をアップロード

```bash
md-to-notion-images <markdown_file> <page_id> --replace-placeholder
```

プレースホルダー `[画像: filename]` を検索し、実画像に置換。

---

## コマンドリファレンス

### md-to-notion-text

```bash
python3 scripts/md_to_notion_text.py <markdown_file> [--placeholder | --no-placeholder]
```

| オプション | 説明 |
|-----------|------|
| `--placeholder` | 画像位置に `[画像: filename]` を挿入（デフォルト） |
| `--no-placeholder` | 画像行を削除 |

### md-to-notion-images

```bash
md-to-notion-images <markdown_file> <page_id> [options]
```

| オプション | 説明 |
|-----------|------|
| `--replace-placeholder` | プレースホルダーを検索して置換 |
| `--dry-run` | アップロードせず確認のみ |

---

## 使用例

### 完全なワークフロー（推奨）

```
ユーザー: .claude/reports/report.md を https://notion.so/xxx にアップロードして

Claude:
1. md_to_notion_text.py で変換
2. Notion MCP (notion-update-page) でテキストアップロード
3. md-to-notion-images で画像アップロード
```

### テキストのみ

```bash
# 変換
python3 scripts/md_to_notion_text.py report.md > /tmp/converted.md

# Notion MCP でアップロード（Claude Codeが実行）
```

### 画像のみ

```bash
md-to-notion-images report.md PAGE_ID
```

---

## ページIDの取得

NotionページのURL末尾32文字がページID:
```
https://www.notion.so/Page-Title-abc123def456...
                                 └─────────────┘
                                   この部分（ハイフンなし）
```

## 前提条件

- `~/.config/notion-image/.env` に `NOTION_TOKEN` を設定
- Notionページで「接続」からIntegrationを追加済み
- notion-image プラグインがインストール済み

## エラー対処

| エラー | 対処 |
|--------|------|
| `401 Unauthorized` | NOTION_TOKENを確認 |
| `404 Not Found` | ページに「接続」からIntegrationを追加 |
| `notion-image not found` | notion-imageプラグインをインストール |
