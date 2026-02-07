---
name: peer-review
description: >
  This skill should be used when the user asks to "review a document",
  "peer review", "professor/student review", "批評レビュー", "文書レビュー",
  "ピアレビュー", "ドキュメントレビュー", or wants critical review of a file
  using a Professor/Student agent team debate pattern.
---

# Peer Review — Professor/Student Agent Team

Professor（批評者）と Student（検証・修正者）の2エージェントチームで文書を批評的にレビューし、改善するスキル。

## ワークフロー

### Step 1: 入力の確認

ユーザーから以下を受け取る:
- **対象ファイルパス**（必須）: レビュー対象のファイル
- **レビュー観点**（任意）: ユーザーが特に注目してほしい点
- **ドメイン**（任意）: 学術サーベイの場合は `references/academic-survey-criteria.md` を参照

対象ファイルを Read で読み、内容を把握する。

### Step 2: レビュー観点の決定

ユーザーが観点を指定しない場合、以下のデフォルト観点を使用:
- オーバーステートメント（過大な主張）
- 論理の飛躍・矛盾
- 情報の不足・欠落
- 構成・表現の改善点

**注意**: 参考文献の実在性・内容記述の正確性は `check-reference` スキルが担当。peer-review では扱わない。

学術サーベイの場合は `references/academic-survey-criteria.md` の観点を追加。

### Step 3: チーム作成

```
TeamCreate:
  team_name: "{filename}-review"  # ファイル名からチーム名を生成
  description: "{filename} のProfessor/Studentレビュー"
```

TaskCreate で2タスクを作成:
1. Professor: 対象ファイルを批評的にレビュー
2. Student: Professorの批評に対応し調査・改善（task 1 にブロックされる）

### Step 4: Professor エージェント起動

```
Task:
  name: professor
  team_name: "{filename}-review"
  subagent_type: general-purpose
  mode: bypassPermissions
  run_in_background: true
```

**Professorプロンプトテンプレート:**

```
あなたは{domain}に精通した厳格な教授です。

チーム名: {team_name}
あなたの名前: professor

## タスク

{file_path} を批評的にレビューしてください。

## レビュー観点

{review_criteria}

## 手順

1. ファイルを読む
2. {verification_tools} で内容を検証する
3. 問題点をカテゴリ別にリストアップする
4. SendMessage で student に批評を送信する
   (type: "message", recipient: "student")
5. Student からの返答を待ち、追加の指摘を行う
6. 3-5ラウンドの議論を行う
7. 修正が十分であれば承認する

## 重要

- 具体的な指摘を含めること（何が間違いで、正しくは何か）
- 曖昧な批判は避け、検証可能な問題を指摘すること
```

### Step 5: Student エージェント起動

```
Task:
  name: student
  team_name: "{team_name}-review"
  subagent_type: general-purpose
  mode: bypassPermissions
  run_in_background: true
```

**Studentプロンプトテンプレート:**

```
あなたは{domain}の研究を行っている大学院生です。

チーム名: {team_name}
あなたの名前: student

## タスク

professor から {file_path} に対する批評が送られてきます。

## 手順

1. professor からのメッセージを待つ
2. {verification_tools} で指摘された内容を検証する
3. 誤りを認め、正確な情報を提示する
4. 反論すべき点は根拠を持って反論する
5. 議論が収束したら、Edit ツールでファイルを修正する
6. 修正完了を professor に報告する
   (SendMessage type: "message", recipient: "professor")

## 重要

- professor からのメッセージを待ってから行動すること
- ファイル修正は議論が十分に行われてから実施すること
- 修正には Edit ツールを使用すること
```

### Step 6: メッセージリレーと監視

team-lead（メインエージェント）として以下を行う:

1. **idle通知の監視**: エージェントが idle になったら、相手にメッセージが届いているか確認
2. **必要時の促し**: メッセージが届いていない場合は SendMessage でリレーする
3. **進捗報告**: ラウンドの進行をユーザーに簡潔に報告する

典型的なフロー:
```
Professor idle (→ student にメッセージ送信済み)
  ↓
Student idle (→ professor に返答送信済み)
  ↓ 必要なら SendMessage で professor に確認を促す
Professor idle (→ Round 2 送信)
  ↓ ...繰り返し...
Professor idle (→ 承認メッセージ)
```

### Step 7: シャットダウン

議論が完了し Professor が承認したら:

1. `SendMessage type: "shutdown_request"` を両エージェントに送信
2. shutdown_approved を確認
3. `TeamDelete` でチームを削除
4. レビュー結果のサマリーをユーザーに報告

## 検証ツールの選択

| ドメイン | Professor/Student が使用するツール |
|---------|----------------------------------|
| 学術サーベイ | Web Search, arXiv MCP (ToolSearch で "arxiv"), WebFetch |
| 技術文書 | Web Search, Grep（コードベース検索） |
| 一般文書 | Web Search |

## 参考資料

### 学術サーベイ向けレビュー観点
`references/academic-survey-criteria.md` — オーバーステートメント検出、比較の公平性、調査範囲の網羅性など学術文献調査に特化した観点を記載。
