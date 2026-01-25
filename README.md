# tk-claude-plugins

tk's personal Claude Code plugins collection.

## Plugins

### 1. codex

Codex CLI を使ったコードレビュー・相談スキル。

**機能:**
- コードレビュー
- 実装方針の相談
- バグの調査
- リファクタリング提案

**前提条件:**
- Codex CLI: `npm install -g @openai/codex`
- OpenAI API Key: 環境変数 `OPENAI_API_KEY` に設定

**使用例:**
```bash
codex exec --full-auto --sandbox read-only --cd /path/to/project "このコードをレビューして"
```

---

### 2. notion-image

Notionに画像を直接アップロードするスキル（Notion File Uploads API使用）。

**機能:**
- ローカル画像をNotion APIで直接アップロード
- 指定したNotionページに画像ブロックとして追加
- 外部ストレージ不要（R2, S3等は不要）

**アーキテクチャ:**
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Claude Code    │────>│ upload_to_notion │────>│   Notion API    │
│                 │     │     .sh          │     │ (File Uploads)  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                 ┌────────▼────────┐
                                                 │  Notion Page    │
                                                 │  (画像ブロック)  │
                                                 └─────────────────┘
```

**セットアップ手順:**

1. **Notion Integrationを作成**
   - https://www.notion.so/my-integrations にアクセス
   - 「New integration」で作成
   - Internal Integration Token（`ntn_`で始まる）をコピー

2. **設定ファイルを作成**
   ```bash
   mkdir -p ~/.config/notion-image
   chmod 700 ~/.config/notion-image
   ```

   `~/.config/notion-image/.env` を作成:
   ```bash
   NOTION_TOKEN=ntn_xxxxxxxxxxxxx
   DEFAULT_PAGE_ID=              # オプション
   ```

   ```bash
   chmod 600 ~/.config/notion-image/.env
   ```

3. **ページにIntegrationを接続**
   - アップロード先のNotionページを開く
   - 右上「...」→「接続」→作成したIntegrationを選択

4. **テスト**
   ```bash
   ~/個人開発/tk-claude-plugins/plugins/notion-image/scripts/upload_to_notion.sh /path/to/image.png PAGE_ID
   ```

**使用例:**
```bash
# 画像をアップロード
./plugins/notion-image/scripts/upload_to_notion.sh /tmp/screenshot.png abc123def456

# 出力例:
# Uploading: /tmp/screenshot.png
#   -> Content-Type: image/png
# Step 1/3: Creating upload object...
#   -> Upload ID: xxx-xxx-xxx
# Step 2/3: Sending file...
#   -> File sent successfully
# Step 3/3: Attaching to page...
#   -> Attached to page: abc123def456
# Upload successful!
```

**制限事項:**
- ファイルサイズ: 20MB以下
- 対応形式: png, jpg, jpeg, gif, webp, svg
- アップロード後1時間以内にページに添付必要

**コスト:** 無料（Notion API追加料金なし）

---

## Installation

このプラグインコレクションをClaude Codeで使用するには、Claude Codeの設定でこのリポジトリを追加してください。

## License

MIT
