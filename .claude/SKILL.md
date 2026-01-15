---
name: OnePaperSlide Builder
description: |
  OnePaperSlideアプリケーション（A3横1枚PowerPoint資料自動生成ツール）の開発を支援するスキル。
  6つの専門サブエージェントを定義し、Streamlit + python-pptx + Gemini APIによる開発をガイドする。

  使用場面:
  - OnePaperSlideの新規機能開発
  - 既存コンポーネントの修正・改善
  - JSONテンプレート・レイアウトエンジンの調整
  - Gemini API連携の最適化
  - テスト・品質改善
---

# OnePaperSlide Builder

公務員向けA3横1枚資料自動生成アプリケーションの開発スキル。

## サブエージェント一覧

| Agent | 担当領域 | 主要ファイル | 詳細ガイド |
|-------|----------|--------------|------------|
| UI-Agent | Streamlit UI | `app.py` | [ui-agent.md](ui-agent.md) |
| Layout-Agent | 座標変換 | `src/layout_engine.py` | [layout-agent.md](layout-agent.md) |
| PPTX-Agent | スライド生成 | `src/pptx_builder.py` | [pptx-agent.md](pptx-agent.md) |
| AI-Agent | Gemini連携 | `src/ai_service.py` | [ai-agent.md](ai-agent.md) |
| Template-Agent | JSON設計 | `templates/`, `components/` | [template-agent.md](template-agent.md) |
| Integration-Agent | テスト | `tests/` | [integration-agent.md](integration-agent.md) |

## 開発フロー

```
Phase 1: 基盤構築
├── UI-Agent → requirements.txt, .gitignore, app.py基本骨格
└── Template-Agent → JSONスキーマ定義

Phase 2: コア機能
├── Layout-Agent → JSON→座標変換ロジック
├── PPTX-Agent → python-pptxスライド生成
└── Template-Agent → T1〜T4テンプレート作成

Phase 3: AI連携
└── AI-Agent → Gemini API統合、プロンプト設計

Phase 4: 統合・検証
└── Integration-Agent → E2Eテスト、品質検証
```

## 使用方法

### 1. 担当エージェントの特定

タスク内容から適切なエージェントを選択:

- **UI関連**（ボタン、入力、表示）→ UI-Agent
- **座標計算・配置**（位置ズレ、余白）→ Layout-Agent
- **スライド描画**（図形、表、フォント）→ PPTX-Agent
- **AI生成品質**（プロンプト、JSON解析）→ AI-Agent
- **テンプレート追加・修正** → Template-Agent
- **バグ調査・テスト** → Integration-Agent

### 2. 詳細ガイド参照

該当エージェントの`*.md`を読み、実装パターンとベストプラクティスを確認。

### 3. 実装・検証

ガイドに従い実装後、Integration-Agentの検証手順でテスト。

## ディレクトリ構成（目標）

```
OnepaperSlide/
├── app.py                    # メインアプリケーション
├── requirements.txt          # 依存パッケージ
├── .gitignore               # セキュリティ設定
├── .streamlit/
│   └── secrets.toml         # APIキー（gitignore対象）
├── src/
│   ├── __init__.py
│   ├── layout_engine.py     # JSONレイアウトエンジン
│   ├── ai_service.py        # Gemini API連携
│   └── pptx_builder.py      # PPTX生成
├── templates/
│   ├── T1_problem_solving.json
│   ├── T2_comparison.json
│   ├── T3_policy_proposal.json
│   └── T4_workflow.json
├── components/
│   ├── table.json
│   ├── flowchart.json
│   └── bullets.json
└── tests/
    └── test_layout_engine.py
```

## 成功指標（SPEC.mdより）

| 指標 | 目標値 |
|------|--------|
| 生成品質 | ベタ書きメモから「9割完成」レベルの資料 |
| レイアウト精度 | 文字被り・図形ズレ発生率 0% |
| 操作性 | 入力→ダウンロードまで3クリック以内 |
| 生成時間 | 30秒以内（1000文字入力時） |
