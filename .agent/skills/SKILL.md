---
name: Skill Router
description: Root skill definition that routes to specialized skills (Frontend, Backend, Verification).
---

# Skill Router

このプロジェクトには、特定のタスク領域に特化した「スキルエージェント」が定義されています。
タスクの内容に応じて、以下のディレクトリにある `SKILL.md` を読み込み、その指示に従ってください。

## 利用可能なスキル

### 1. 🎨 Frontend Developer Skill

- **Path:** `.agent/skills/frontend/SKILL.md`
- **用途:**
  - UI の実装、修正、スタイリング
  - React コンポーネントの作成
  - レスポンシブ対応、デザイン調整

### 2. ⚙️ Backend Developer Skill

- **Path:** `.agent/skills/backend/SKILL.md`
- **用途:**
  - API エンドポイントの実装
  - データベース設計、マイグレーション
  - ビジネスロジック、データ処理

### 3. ✅ Verification Skill

- **Path:** `.agent/skills/verification/SKILL.md`
- **用途:**
  - テストの作成と実行
  - バグの調査・修正（再現スクリプト作成）
  - 品質チェック、E2E テスト

## 共通ルール

すべてのスキルは、以下の共通コンテキストを尊重する必要があります：

- `SPEC.md`: プロジェクト全体の仕様
- `.gemini/GEMINI.md`: ユーザー定義のグローバルルール（日本語推奨など）

## 使い方

タスクを開始する際、まず自分の役割（Frontend/Backend/Verification）を判断し、対応する `SKILL.md` を `view_file` してください。
