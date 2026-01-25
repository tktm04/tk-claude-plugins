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

### 2. notion-r2-image

Notionに画像をアップロードするためのスキル（Cloudflare R2 + Workers経由）。

**機能:**
- ローカル画像をCloudflare R2（プライベートバケット）にアップロード
- Cloudflare Workers経由でトークン認証付きURLを生成
- NotionページにそのURLを埋め込み可能

**アーキテクチャ:**
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Claude Code    │────>│ upload_to_r2.sh  │────>│   Cloudflare    │
│                 │     │ (AWS Sig V4)     │     │   R2 (PRIVATE)  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
┌─────────────────┐     ┌──────────────────┐              │
│   Notion Page   │<────│ Workers Proxy    │<─────────────┘
│                 │     │ (token auth)     │
└─────────────────┘     └──────────────────┘
```

**セキュリティ:**
- R2バケットは非公開（直接アクセス不可）
- Workers経由で固定トークン認証（`?token=xxx`）
- トークンを知らないとアクセスできない

**セットアップ手順:**

1. **Cloudflare R2バケットを作成**
   - Cloudflare Dashboard > R2 > Create bucket
   - バケットは**プライベート**設定のまま

2. **R2 APIトークンを取得**
   - R2 > Manage R2 API Tokens > Create API Token
   - Object Read & Write 権限を付与

3. **設定ファイルを作成**
   ```bash
   mkdir -p ~/.config/notion-r2-image
   ```

   `~/.config/notion-r2-image/.env` を作成:
   ```bash
   R2_ACCESS_KEY_ID=your_access_key
   R2_SECRET_ACCESS_KEY=your_secret_key
   R2_BUCKET_NAME=your-bucket-name
   R2_ACCOUNT_ID=your_account_id
   WORKERS_PROXY_URL=https://your-worker.workers.dev
   WORKERS_AUTH_TOKEN=your_secret_token  # openssl rand -hex 32 で生成
   ```

4. **Cloudflare Workersをデプロイ**
   ```bash
   cd plugins/notion-r2-image/workers
   npm install -g wrangler
   wrangler login

   # wrangler.toml の bucket_name を編集

   # 認証トークンを設定
   wrangler secret put AUTH_TOKEN
   # プロンプトでトークンを入力

   # デプロイ
   wrangler deploy
   ```

5. **テスト**
   ```bash
   chmod +x plugins/notion-r2-image/scripts/upload_to_r2.sh
   ./plugins/notion-r2-image/scripts/upload_to_r2.sh /path/to/image.png
   ```

**使用例:**
```bash
# 画像をアップロード
./plugins/notion-r2-image/scripts/upload_to_r2.sh /tmp/screenshot.png

# 出力例:
# Upload successful!
# Notion URL: https://your-worker.workers.dev/images/20240115_143052_screenshot.png?token=xxx
```

出力されたURLをNotionの画像ブロック（`/image`）に貼り付けて使用。

---

## Installation

このプラグインコレクションをClaude Codeで使用するには、Claude Codeの設定でこのリポジトリを追加してください。

## License

MIT
