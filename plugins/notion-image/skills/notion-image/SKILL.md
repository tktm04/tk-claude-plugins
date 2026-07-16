---
name: notion-image
description: "画像ファイルをNotionに直接アップロードする。使用場面: Notionに画像を追加したい時、スクリーンショットを共有したい時。トリガー: notion画像, 画像アップロード, Notionにアップロード"
allowed-tools: "Bash(notion-upload:*), Bash(notion-get-blocks:*)"
---

# Notion Image Upload

画像をNotionページに直接アップロードするスキル。外部ストレージ不要。

## クイック判断フロー

```
画像をNotionにアップロードしたい
         │
         ├── ページ末尾に追加したい
         │   └── notion-upload <image> [page_id]
         │
         ├── 特定の場所に挿入したい
         │   ├── 1. notion-get-blocks <page_id>  # ブロックID確認
         │   └── 2. notion-upload <image> <page_id> --after <block_id>
         │
         └── キャプション付きで追加したい
             └── notion-upload <image> [page_id] --caption "説明文"
```

## 典型ユースケース

### 実験記録に結果画像を追加

```bash
# 「実験結果」セクションの下に画像を挿入したい場合
# 1. ブロック一覧を取得してセクションのIDを見つける
notion-get-blocks abc123def456

# 出力例:
#   heading_2: 実験結果 (block_id: xxx111)
#   paragraph: 考察テキスト... (block_id: xxx222)

# 2. 「実験結果」見出しの直後に画像を挿入
notion-upload /tmp/result.png abc123def456 --after xxx111 --caption "Figure 1: 実験結果"
```

### ドキュメントにスクリーンショットを添付

```bash
# ページ末尾に追加（最もシンプル）
notion-upload ~/Desktop/screenshot.png abc123def456
```

### 複数画像を順番に追加

```bash
# 1枚目を追加
notion-upload /tmp/step1.png PAGE_ID --caption "Step 1"

# 2枚目以降は前の画像の後に挿入
notion-get-blocks PAGE_ID  # 1枚目のblock_idを確認
notion-upload /tmp/step2.png PAGE_ID --after <1枚目のblock_id> --caption "Step 2"
```

## コマンドリファレンス

### notion-upload

```bash
notion-upload <image_path> [page_id] [--after <block_id>] [--caption <text>]
```

| 引数/オプション | 説明 |
|---------------|------|
| `<image_path>` | 画像ファイルパス（png/jpg/gif/webp/svg） |
| `[page_id]` | 対象ページID（省略時はDEFAULT_PAGE_ID） |
| `--after <block_id>` | 指定ブロックの直後に挿入 |
| `--caption <text>` | 画像のキャプション |

### notion-get-blocks

```bash
notion-get-blocks <page_id>
```

ページ内のブロック一覧とIDを表示。`--after`で使用するblock_idを確認する。

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

## エラー対処

| エラー | 対処 |
|--------|------|
| `401 Unauthorized` | NOTION_TOKENを確認（`ntn_`で始まる） |
| `404 Not Found` | ページに「接続」からIntegrationを追加 |
| `File not found` | 画像ファイルパスを確認 |
