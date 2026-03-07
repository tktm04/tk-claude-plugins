---
name: gemini
description: "Gemini CLI を使用したコードレビュー・分析・相談を実行する。使用場面: コードレビュー依頼時、実装方針の相談、バグの調査、リファクタリング提案、解消が難しい問題の調査。トリガー: gemini, geminiでレビュー, geminiに相談"
allowed-tools: "Bash(gemini:*)"
---

# Gemini

Gemini CLI を使用してコードレビュー・分析・相談を実行するスキル。

## 前提条件

- **Gemini CLI** がインストールされていること
  - インストール: `npm install -g @google/gemini-cli`
  - バージョン確認: `gemini --version`
- **Google AI API キー** が設定されていること（または Google Cloud 認証）

## 実行コマンド

```bash
gemini -p "<request>"
```

## パラメータ

| パラメータ | 説明 |
|-----------|------|
| `-p "<prompt>"` | プロンプト（依頼内容、日本語可） |
| `-m <model>` | モデル指定（オプション） |

## 使用例

### コードレビュー
```bash
gemini -p "このプロジェクトのコードをレビューして、改善点を指摘してください"
```

### 設計相談
```bash
gemini -p "この認証機能の設計方針について意見をください"
```

### バグ調査
```bash
gemini -p "このエラーの原因を調査してください: <error_message>"
```

### セキュリティチェック
```bash
gemini -p "セキュリティ上の問題点がないかチェックしてください"
```

## 実行手順

1. ユーザーから依頼内容を受け取る
2. 上記コマンド形式で Gemini を実行
3. Gemini の出力をリアルタイムで表示
4. 結果をユーザーに報告

## 注意事項

- Gemini CLI が事前にインストールされている必要があります
- 複雑な調査は時間がかかる場合があります
- Gemini の意見を鵜呑みにせず、最終判断は自分で行ってください

## トラブルシューティング

### よくあるエラーと対処法

| エラー | 原因 | 対処法 |
|--------|------|--------|
| `command not found: gemini` | Gemini CLI 未インストール | `npm install -g @google/gemini-cli` を実行 |
| `Authentication error` | 認証未設定 | Google Cloud 認証または API キーを設定 |
| `Timeout` | 分析に時間がかかりすぎ | リクエストを小さく分割 |

## ラッパースクリプト

より簡単に実行するためのラッパースクリプトが用意されています:

```bash
gemini-review "リクエスト内容"
```

設定ファイル（`~/.config/gemini/.env`）でモデルを指定できます:

```bash
GEMINI_MODEL=gemini-pro
```
