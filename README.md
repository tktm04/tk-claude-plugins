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
./scripts/setup.sh notion-image  # notion-markdown も含む
./scripts/setup.sh writing  # cognitive-rhythm-writing と japanese-tech-writing の両方を含む
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
./scripts/setup.sh notion-image  # notion-image と notion-markdown の両方をセットアップ
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

# Markdownファイル（テキスト＋画像）をNotionにアップロード（推奨）
md-to-notion report.md PAGE_ID  # 1コマンドでテキスト＋画像をアップロード

# 個別に処理する場合
md-to-notion-text report.md > /tmp/converted.md  # プレースホルダー付きMarkdownに変換
md-to-notion-images report.md PAGE_ID --replace-placeholder  # 画像をアップロード
```

> 相対リンク（例: `[研究計画書](proposal.md)`）はNotionで `Invalid URL` になるため、自動的にリンクテキストのみ残すよう変換されます。

**前提条件（notion-markdown）:**
- Python 3.9+（標準ライブラリのみ使用、追加インストール不要）

**制限事項:**
- ファイルサイズ: 20MB以下
- 対応形式: png, jpg, jpeg, gif, webp, svg
- アップロード後1時間以内にページに添付必要

**コスト:** 無料（Notion API追加料金なし）

---

### 4. writing

日本語の執筆規範スキル（`cognitive-rhythm-writing` / `japanese-tech-writing`）。

**機能:**
- `japanese-tech-writing`：技術文書の整形（一文一行、脚注等）、パラグラフライティング、論証の厳密さ、冗長・LLMっぽい空句の排除
- `cognitive-rhythm-writing`：説明文に緩急（認知モードの切替）を設計し、平坦な文章を診断・修正する。作業前に `japanese-tech-writing` を読む前提

**セットアップ:**
```bash
./scripts/setup.sh writing
```

**手動ステップ:** なし（スクリプト・APIキー不要）

**使用例:**
```
「この草稿を日本語技術文書の規範でリライトして」
「この章、緩急をつけて読み物っぽくして」
```

出典: [cognitive-rhythm-writing](https://gist.github.com/k16shikano/eb2929f13ed19c97188393d297be8432), [japanese-tech-writing](https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d)

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
ln -sf /path/to/tk-claude-plugins/plugins/writing/skills/cognitive-rhythm-writing ~/.claude/skills/cognitive-rhythm-writing
ln -sf /path/to/tk-claude-plugins/plugins/writing/skills/japanese-tech-writing ~/.claude/skills/japanese-tech-writing
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

# writing
「この草稿を日本語技術文書の規範でリライトして」
「この章、緩急をつけて読み物っぽくして」
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
md-to-notion report.md PAGE_ID  # 推奨: 1コマンドで完結
```

## License

MIT
