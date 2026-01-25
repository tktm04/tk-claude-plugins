# Notion Image Upload セットアップ

## 概要

Notion File Uploads APIを使用して画像を直接アップロードする機能。
外部ストレージ（R2, S3等）は不要。

## アーキテクチャ

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Claude Code    │────>│  notion-upload   │────>│   Notion API    │
│                 │     │                  │     │ (File Uploads)  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                 ┌────────▼────────┐
                                                 │  Notion Page    │
                                                 │  (画像ブロック)  │
                                                 └─────────────────┘
```

## クイックセットアップ

```bash
# リポジトリのルートで実行
./scripts/setup.sh notion-image

# シェル設定を反映
source ~/.zshrc
```

セットアップスクリプトが自動で:
- 設定ディレクトリ作成（`~/.config/notion-image`）
- 設定ファイルテンプレート作成
- シンボリックリンク作成（`~/bin/notion-upload`）
- PATH設定を `~/.zshrc` に追加

## 手動ステップ

### 1. Notion Integrationを作成

1. https://www.notion.so/my-integrations にアクセス
2. 「New integration」をクリック
3. 名前を入力（例: `Image Uploader`）
4. 関連ワークスペースを選択
5. 「Submit」をクリック
6. 「Capabilities」で以下を有効化:
   - ☑️ Read content
   - ☑️ Insert content
7. **Internal Integration Token** をコピー（`ntn_`で始まる）

### 2. トークンを設定ファイルに記入

```bash
# 設定ファイルを編集
nano ~/.config/notion-image/.env
```

`NOTION_TOKEN=ntn_xxxxxxxxxxxxx` の部分を編集

### 3. ページにIntegrationを接続

1. アップロード先のNotionページを開く
2. 右上の「...」→「接続」をクリック
3. 作成したIntegrationを選択

## 使用方法

```bash
# ページIDを指定
notion-upload /path/to/image.png PAGE_ID

# デフォルトページを設定済みの場合
notion-upload /path/to/image.png
```

## ページIDの取得方法

1. NotionでページURLをコピー
2. 例: `https://www.notion.so/My-Page-abc123def456789...`
3. 末尾32文字（ハイフンなし）がページID

## トラブルシューティング

### 401 Unauthorized
- トークンが正しいか確認
- `ntn_`で始まっているか確認

### 404 Not Found
- ページにIntegrationが接続されているか確認
- 「...」→「接続」でIntegrationを追加

### command not found: notion-upload
- `source ~/.zshrc` を実行
- シンボリックリンク確認: `ls -la ~/bin/notion-upload`

### Upload expires
- アップロード後1時間以内にページに添付する必要あり
- page_idを指定して再実行

## 制限事項

- ファイルサイズ: 20MB以下（それ以上はマルチパートが必要）
- 対応形式: png, jpg, jpeg, gif, webp, svg
- 1時間制限: アップロード後1時間以内に添付必要

## コスト

**無料** - Notion APIは追加料金なし。
