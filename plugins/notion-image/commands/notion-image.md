---
description: 画像をNotionに直接アップロード
---

# Notion Image Upload

画像ファイルをNotion File Uploads APIで直接アップロードします。

## 実行方法

```bash
~/個人開発/tk-claude-plugins/plugins/notion-image/scripts/upload_to_notion.sh <image_file_path> [page_id]
```

## 手順

1. ユーザーから画像ファイルパスを受け取る
2. ページIDを確認（指定がなければDEFAULT_PAGE_ID使用）
3. ファイルが存在し、対応形式（png, jpg, gif, webp, svg）であることを確認
4. upload_to_notion.sh を実行
5. 結果をユーザーに報告

## 前提条件

- `~/.config/notion-image/.env` にNOTION_TOKENが設定済み
- 対象ページでIntegrationが「接続」されている

## 出力例

```
Uploading: /tmp/screenshot.png
  -> Content-Type: image/png
Step 1/3: Creating upload object...
  -> Upload ID: abc123...
Step 2/3: Sending file...
  -> File sent successfully
Step 3/3: Attaching to page...
  -> Attached to page: xyz789...
Upload successful!
```
