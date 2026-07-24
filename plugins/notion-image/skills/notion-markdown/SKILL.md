---
name: notion-markdown
description: "Markdownファイル（テキスト + 画像）をNotionページにアップロードする。使用場面: レポートやドキュメントをNotionに公開したい時。トリガー: md-to-notion, markdown notion, mdアップロード, notionに公開"
allowed-tools: "Bash(md-to-notion:*), Bash(md-to-notion-text:*), Bash(md-to-notion-images:*), Read"
---

# Markdown to Notion Upload

Markdownファイル（テキスト + 画像）をNotionページにアップロードするスキル。

## 推奨: 統合コマンド（1コマンドで完結）

```bash
md-to-notion <markdown_file> <page_id>
```

これだけで：
1. Markdownを解析してNotionブロックに変換
2. ページにテキストをアップロード
3. 画像を自動でアップロード・置換

**Claude Code経由でも最小トークン消費で実行可能。**

### オプション

| オプション | 説明 |
|-----------|------|
| `--dry-run` | アップロードせず確認のみ |
| `--append` | 既存コンテンツに追記（デフォルトは置換） |
| `--no-title` | 先頭の `# 見出し` をページタイトルに反映しない |

**注意: 実行はバックグラウンド推奨。** 画像アップロード・ブロック分割・Notion API 呼び出しで数十秒〜数分かかるため、Claude Code から実行する際は Bash tool の `run_in_background: true` を指定する。`--dry-run` は短時間で終わるので前景実行で OK。

---

## 対応する Markdown 要素

`md-to-notion` は以下の Markdown 要素を対応する Notion ブロックに変換する。

| Markdown | Notion ブロック |
|----------|----------------|
| `#`〜`######` 見出し | heading_1〜3（4 以降は 3 に丸め） |
| 箇条書き / 番号付きリスト（ネスト可） | bulleted / numbered list |
| **太字** / *斜体* / `インラインコード` / [リンク](url) | rich text annotations |
| ` ```lang ` コードブロック | code ブロック（言語名を正規化） |
| **GFM パイプテーブル** | **Notion table ブロック**（`\|---\|` セパレータ行の列数を正準列数とする。エスケープ `\|`・インラインコード内・太字内の `\|` も正しく処理） |
| 画像セルを含むテーブル | column_list（table はセル内画像を持てないため） |
| `> 引用` | quote ブロック（複数行対応） |
| `$インライン数式$` / `$$ブロック数式$$` | equation（KaTeX 式） |
| `<details><summary>` | toggle（heading_3, `is_toggleable`） |
| `![alt](path)` 画像 | image ブロック（自動アップロード） |

**パイプテーブルはサポート対象。** 旧バージョンでは非対応だったため、テーブルをリスト形式に手動変換していた運用は不要。ただしセル内に画像を含む場合のみ column_list に変換される。

---

## 個別コマンド（高度な使用）

テキストと画像を別々に処理したい場合：

### Step 1: Markdownをプレースホルダー付きで変換

```bash
md-to-notion-text <markdown_file> > /tmp/converted.md
```

### Step 2: Notion MCPでテキストをアップロード

```
notion-update-page を使用:
- page_id: 対象ページID
- command: replace_content（全置換）または insert_content（追記）
- new_str（replace_content の場合）/ content（insert_content の場合）: /tmp/converted.md の内容（Notion-flavored Markdown）
```

新規ページを作成してから流し込む場合は、`notion-create-pages` で親ページ配下に空ページを作成 → `md-to-notion <file> <新ページID>` の順が最も確実（統合コマンドが置換まで一括で行う）。

### Step 3: 画像をアップロード

```bash
md-to-notion-images <markdown_file> <page_id> --replace-placeholder
```

---

## コマンドリファレンス

### md-to-notion-text

```bash
md-to-notion-text <markdown_file> [--no-placeholder]
```

| オプション | 説明 |
|-----------|------|
| (なし) | 画像位置に `[画像: filename]` を挿入（デフォルト） |
| `--no-placeholder` | 画像行を削除 |

- 相対リンク（例: `[研究計画書](proposal.md)`）は自動でリンクテキストのみを残し、Notionの `Invalid URL` エラーを回避

### md-to-notion-images

```bash
md-to-notion-images <markdown_file> <page_id> [options]
```

| オプション | 説明 |
|-----------|------|
| `--replace-placeholder` | プレースホルダーを検索して置換 |
| `--dry-run` | アップロードせず確認のみ |

---

## 使い分けガイド

### 基本: 統合コマンドを使う（推奨）

```
ユーザー: report.md を https://notion.so/xxx にアップロードして

Claude:
md-to-notion report.md PAGE_ID
```

**統合コマンドを使う場面:**
- 通常のMarkdownアップロード
- テキスト＋画像を一括処理したい
- トークン消費を抑えたい

### 応用: 個別コマンドを使う

**個別コマンドを使う場面:**
- テキストのみ先にアップロードしたい
- 画像のみ追加したい
- Notion MCP で高度な操作（特定ブロック指定など）が必要
- 途中でエラーになった場合のリカバリ

```bash
# テキストのみ
md-to-notion-text report.md > /tmp/converted.md
# → Notion MCPでアップロード

# 画像のみ（既存ページのプレースホルダーを置換）
md-to-notion-images report.md PAGE_ID --replace-placeholder
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

- Python 3.9+（標準ライブラリのみ使用、追加インストール不要）
- `~/.config/notion-image/.env` に `NOTION_TOKEN` を設定
- Notionページで「接続」からIntegrationを追加済み
- notion-image プラグインがインストール済み (`scripts/setup.sh notion-image`)

## エラー対処

| エラー | 対処 |
|--------|------|
| `401 Unauthorized` | NOTION_TOKENを確認 |
| `404 Not Found` | ページに「接続」からIntegrationを追加 |
| `notion-image not found` | notion-imageプラグインをインストール |
