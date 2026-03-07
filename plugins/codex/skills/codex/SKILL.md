---
name: codex
description: "Codex CLI を使用したコードレビュー・分析・相談を実行する。使用場面: コードレビュー依頼時、実装方針の相談、バグの調査、リファクタリング提案、解消が難しい問題の調査。トリガー: codex, コードレビュー, レビューして, 相談して"
allowed-tools: "Bash(codex:*)"
---

# Codex

Codex CLI を使用してコードレビュー・分析・相談を実行するスキル。

## 前提条件

- **Codex CLI** がインストールされていること
  - インストール: `npm install -g @openai/codex`
  - バージョン確認: `codex --version`
  - 推奨バージョン: v0.39.0 以上
- **OpenAI API キー** が設定されていること
  - 環境変数 `OPENAI_API_KEY` に設定

## 実行コマンド

```bash
codex exec --full-auto --sandbox read-only --cd <project_directory> "<request>"
```

## パラメータ

| パラメータ | 説明 |
|-----------|------|
| `--full-auto` | 完全自動モードで実行 |
| `--sandbox read-only` | 読み取り専用サンドボックス（安全な分析用） |
| `--cd <dir>` | 対象プロジェクトのディレクトリ |
| `"<request>"` | 依頼内容（日本語可） |

## サンドボックスモード

| モード | 説明 | 用途 |
|--------|------|------|
| `read-only` | ファイルの読み取りのみ許可 | コードレビュー、分析、相談（推奨） |
| `workspace-write` | ワークスペース内への書き込みを許可 | リファクタリング実行、テスト実行 |
| `full-write` | すべての書き込みを許可 | 危険 - 通常は使用しない |

**注意**: 書き込みモードを使用する場合は、意図しない変更が行われるリスクがあります。必ず Git でコミット済みの状態で実行し、変更内容を確認してください。

## パスとリクエストの指定

### パスにスペースが含まれる場合
```bash
codex exec --full-auto --sandbox read-only --cd "/path/with spaces/project" "リクエスト内容"
```

### 複数行のリクエスト
```bash
codex exec --full-auto --sandbox read-only --cd /path/to/project "$(cat <<'EOF'
以下のファイルをレビューしてください:
- src/main.ts
- src/utils.ts
改善点と問題点を指摘してください。
EOF
)"
```

### デフォルトディレクトリ
`--cd` を省略すると、カレントディレクトリが使用されます。

## 使用例

### コードレビュー
```bash
codex exec --full-auto --sandbox read-only --cd /path/to/project "このプロジェクトのコードをレビューして、改善点を指摘してください"
```

### 設計相談
```bash
codex exec --full-auto --sandbox read-only --cd /path/to/project "この認証機能の設計方針について意見をください"
```

### バグ調査
```bash
codex exec --full-auto --sandbox read-only --cd /path/to/project "このエラーの原因を調査してください: <error_message>"
```

### セキュリティチェック
```bash
codex exec --full-auto --sandbox read-only --cd /path/to/project "セキュリティ上の問題点がないかチェックしてください"
```

## 実行手順

1. ユーザーから依頼内容を受け取る
2. 対象プロジェクトのディレクトリを特定する（通常はカレントディレクトリ）
3. 上記コマンド形式で Codex を実行
4. Codex の出力をリアルタイムで表示
5. 結果をユーザーに報告

## 注意事項

- Codex CLI が事前にインストールされている必要があります
- `--sandbox read-only` により、Codex はファイルの読み取りのみ可能です（安全）
- 複雑な調査は時間がかかる場合があります
- Codex の意見を鵜呑みにせず、最終判断は自分で行ってください

## トラブルシューティング

### よくあるエラーと対処法

| エラー | 原因 | 対処法 |
|--------|------|--------|
| `command not found: codex` | Codex CLI 未インストール | `npm install -g @openai/codex` を実行 |
| `Error: Missing API key` | API キー未設定 | `export OPENAI_API_KEY=your-key` を設定 |
| `Permission denied` | ディレクトリへのアクセス権限なし | パスの権限を確認、または `sudo` で実行 |
| `Timeout` | 分析に時間がかかりすぎ | リクエストを小さく分割、または対象ファイルを限定 |

### 終了コード

| コード | 意味 |
|--------|------|
| `0` | 正常終了 |
| `1` | 一般的なエラー |
| `2` | 引数エラー |

### 長時間実行への対応

複雑なコードベースの分析は時間がかかる場合があります。以下の方法で効率化できます：

- 対象ディレクトリを限定する（例: `--cd /project/src` でソースのみ）
- リクエストを具体的にする（例: 「認証モジュールのセキュリティをチェック」）
- `.codexignore` ファイルで不要なファイルを除外する
