# tk-claude-plugins

Claude Code plugins collection.

## Quick Start

```bash
# リポジトリをクローン
git clone https://github.com/your-username/tk-claude-plugins.git
cd tk-claude-plugins

# 全プラグインをセットアップ
./scripts/setup.sh all

# または個別にセットアップ
./scripts/setup.sh codex
./scripts/setup.sh gemini
./scripts/setup.sh notion-image
```

セットアップ後、**Claude Codeを再起動**するとスキルが認識されます。

セットアップスクリプトが自動で:
- `~/.claude/skills/` にスキルを登録
- 設定ディレクトリ作成
- 設定ファイルテンプレート作成
- コマンドのPATH追加
- 残りの手動ステップを案内

---

## Plugins

### 1. codex

Codex CLI を使ったコードレビュー・相談スキル。

**機能:**
- コードレビュー
- 実装方針の相談
- バグの調査
- リファクタリング提案

**セットアップ:**
```bash
./scripts/setup.sh codex
```

**手動ステップ:**

1. **Codex CLIをインストール**
   ```bash
   npm install -g @openai/codex
   ```

2. **APIキーを設定**
   ```bash
   echo 'export OPENAI_API_KEY=sk-xxx' >> ~/.zshrc
   source ~/.zshrc
   ```

**使用例:**
```bash
# ラッパースクリプト
codex-review "このコードをレビューして"

# 直接実行
codex exec --full-auto --sandbox read-only --cd /path/to/project "このコードをレビューして"
```

**設定ファイル:** `~/.config/codex/.env`
```bash
# サンドボックスモード: read-only | workspace-write | full-write
CODEX_SANDBOX=read-only
```

---

### 2. gemini

Gemini CLI を使ったコードレビュー・相談スキル。

**機能:**
- コードレビュー
- 実装方針の相談
- バグの調査
- リファクタリング提案

**セットアップ:**
```bash
./scripts/setup.sh gemini
```

**手動ステップ:**

1. **Gemini CLIをインストール**
   ```bash
   npm install -g @google/gemini-cli
   ```

2. **Google認証を設定**（初回実行時に自動で認証フローが開始）

**使用例:**
```bash
# ラッパースクリプト
gemini-review "このコードをレビューして"

# 直接実行
gemini -p "このコードをレビューして"
```

**設定ファイル:** `~/.config/gemini/.env`
```bash
# モデル指定（空欄でデフォルト）
GEMINI_MODEL=
```

---

### 3. notion-image

Notionに画像を直接アップロードするスキル（Notion File Uploads API使用）。

**機能:**
- ローカル画像をNotion APIで直接アップロード
- 指定したNotionページに画像ブロックとして追加
- **Markdownファイル（テキスト＋画像）をNotionページにアップロード** (`/notion-markdown`)
- 外部ストレージ不要（R2, S3等は不要）

**アーキテクチャ:**
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

**セットアップ:**
```bash
./scripts/setup.sh notion-image
```

**手動ステップ:**

1. **Notion Integrationを作成**
   - https://www.notion.so/my-integrations にアクセス
   - 「New integration」→ 名前入力 → Submit
   - Capabilities: Read content ✅, Insert content ✅
   - トークン（`ntn_xxx...`）をコピー

2. **トークンを設定ファイルに記入**
   ```bash
   # ntn_xxx... の部分をコピーしたトークンに置き換えて実行
   echo "NOTION_TOKEN=ntn_xxxxxxxxxxxxx" > ~/.config/notion-image/.env
   ```

3. **Notionでページに接続**
   - アップロード先ページを開く → 右上「...」→「接続」→ Integration選択

**使用例:**
```bash
# 画像をページ末尾にアップロード
notion-upload /tmp/screenshot.png PAGE_ID

# ブロックIDを取得（特定位置に挿入する場合）
notion-get-blocks PAGE_ID

# 特定ブロックの後に挿入
notion-upload /tmp/screenshot.png PAGE_ID --after BLOCK_ID

# キャプション付きで挿入（キャプションは画像の上に表示）
notion-upload /tmp/screenshot.png PAGE_ID --after BLOCK_ID --caption "Figure 1"

# Markdownファイル（テキスト＋画像）をNotionにアップロード
md-to-notion-text report.md > /tmp/converted.md  # プレースホルダー付きMarkdownに変換
md-to-notion-images report.md PAGE_ID --replace-placeholder  # 画像をアップロード
```

**前提条件（notion-markdown）:**
- Python 3.9+（標準ライブラリのみ使用、追加インストール不要）

**制限事項:**
- ファイルサイズ: 20MB以下
- 対応形式: png, jpg, jpeg, gif, webp, svg
- アップロード後1時間以内にページに添付必要

**コスト:** 無料（Notion API追加料金なし）

---

## Claude Codeへの登録

セットアップスクリプトが自動で `~/.claude/skills/` にスキルを登録します：

```bash
./scripts/setup.sh all
```

登録後、**Claude Codeを再起動**するとスキルが認識されます。

手動で登録する場合：

```bash
mkdir -p ~/.claude/skills
ln -sf /path/to/tk-claude-plugins/plugins/codex/skills/codex ~/.claude/skills/codex
ln -sf /path/to/tk-claude-plugins/plugins/gemini/skills/gemini ~/.claude/skills/gemini
ln -sf /path/to/tk-claude-plugins/plugins/notion-image/skills/notion-image ~/.claude/skills/notion-image
ln -sf /path/to/tk-claude-plugins/plugins/notion-image/skills/notion-markdown ~/.claude/skills/notion-markdown
```

## Usage

Claude Codeで以下のように使用:

```
# codex
「codexでこのコードをレビューして」
「codexに相談して」

# gemini
「geminiでこのコードをレビューして」
「geminiに相談して」

# notion-image
「この画像をNotionにアップロードして」
/notion-image /path/to/image.png PAGE_ID

# notion-markdown
「このMarkdownをNotionにアップロードして」
/notion-markdown report.md PAGE_ID
```

コマンドラインからも使用可能:

```bash
# codex
codex-review "このコードをレビューして"

# gemini
gemini-review "このコードをレビューして"

# notion-image
notion-upload /path/to/image.png PAGE_ID
notion-get-blocks PAGE_ID  # ブロックID取得

# notion-markdown
md-to-notion-text report.md > /tmp/converted.md
md-to-notion-images report.md PAGE_ID --replace-placeholder
```

## License

MIT
