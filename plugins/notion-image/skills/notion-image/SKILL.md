---
name: notion-image
description: 画像をNotionに直接アップロード。使用場面: (1) Notionに画像を追加したい時、(2) スクリーンショットを共有したい時。トリガー: "notion画像", "画像アップロード", "/notion-image"
---

# Notion Image Upload

画像ファイルをNotion File Uploads APIで直接アップロードし、指定ページに埋め込むスキル。
外部ストレージ（R2, S3等）は不要。

## 前提条件

- **設定ファイル** が存在すること
  - パス: `~/.config/notion-image/.env`
  - 必須変数: `NOTION_TOKEN`
  - オプション: `DEFAULT_PAGE_ID`

- **Notion Integration** が設定されていること
  - https://www.notion.so/my-integrations でIntegration作成
  - 対象ページで「接続」からIntegrationを追加

- **依存ツール** がインストールされていること
  - `curl`

## 実行コマンド

```bash
~/個人開発/tk-claude-plugins/plugins/notion-image/scripts/upload_to_notion.sh <image_file_path> [page_id]
```

## パラメータ

| パラメータ | 必須 | 説明 |
|-----------|------|------|
| `<image_file_path>` | ○ | アップロードする画像ファイルのパス |
| `[page_id]` | △ | 画像を追加するNotionページID（省略時はDEFAULT_PAGE_ID使用） |

## 出力形式

成功時:
```
Uploading: /path/to/image.png
  -> Content-Type: image/png
Step 1/3: Creating upload object...
  -> Upload ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Step 2/3: Sending file...
  -> File sent successfully
Step 3/3: Attaching to page...
  -> Attached to page: abc123...
Upload successful!
```

## 対応ファイル形式

| 形式 | MIME Type |
|------|-----------|
| `.png` | image/png |
| `.jpg`, `.jpeg` | image/jpeg |
| `.gif` | image/gif |
| `.webp` | image/webp |
| `.svg` | image/svg+xml |

## 使用例

### 基本的な使用

```bash
# デフォルトページにアップロード
~/個人開発/tk-claude-plugins/plugins/notion-image/scripts/upload_to_notion.sh /tmp/screenshot.png

# 特定ページにアップロード
~/個人開発/tk-claude-plugins/plugins/notion-image/scripts/upload_to_notion.sh /tmp/screenshot.png abc123def456
```

### Claude Codeでの使用

ユーザー: 「この画像をNotionにアップロードして」
→ ページIDを確認し、スキルを実行

ユーザー: 「スクリーンショットをNotionページXXXに追加して」
→ ページIDとファイルパスを特定し、スキルを実行

## ページIDの取得方法

1. Notionでページを開く
2. URLをコピー（例: `https://www.notion.so/Page-Title-abc123def456...`）
3. 末尾32文字がページID（ハイフンなしで使用）

## エラーハンドリング

| エラー | 原因 | 対処法 |
|--------|------|--------|
| `Config file not found` | 設定ファイル未作成 | `~/.config/notion-image/.env` を作成 |
| `NOTION_TOKEN not set` | トークン未設定 | .envにNOTION_TOKENを追加 |
| `File not found` | 指定ファイルが存在しない | ファイルパスを確認 |
| `Unsupported file type` | 非対応の画像形式 | png/jpg/gif/webp/svgを使用 |
| `Failed to create file upload` | API認証エラー | トークンを確認 |
| `Failed to attach image` | ページ接続エラー | ページにIntegrationを接続 |

## 注意事項

- **1時間制限**: アップロード後1時間以内にページに添付する必要あり
- **ファイルサイズ**: 20MB以下（それ以上はマルチパート必要）
- **Integration接続必須**: 対象ページで「接続」からIntegrationを追加すること

## トラブルシューティング

### 401 Unauthorized
- NOTION_TOKENが正しいか確認
- トークンが`ntn_`で始まっているか確認

### 404 Not Found
- ページにIntegrationが接続されているか確認
- Notionページ右上の「...」→「接続」→対象Integrationを追加

### ページIDが見つからない
- NotionページのURLから末尾32文字を抽出
- ハイフンを除去して使用
