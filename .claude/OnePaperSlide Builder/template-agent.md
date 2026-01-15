# Template-Agent: JSONテンプレート設計ガイド

## 担当ファイル

- `templates/T1_problem_solving.json` - 問題解決型
- `templates/T2_comparison.json` - 比較検討型
- `templates/T3_policy_proposal.json` - 施策提案型
- `templates/T4_workflow.json` - 業務フロー型
- `components/table.json` - 表コンポーネント
- `components/flowchart.json` - フローチャートコンポーネント
- `components/bullets.json` - 箇条書きコンポーネント

## 目次

1. [設計思想](#1-設計思想)
2. [デザイン仕様](#2-デザイン仕様)
3. [テンプレートスキーマ](#3-テンプレートスキーマ)
4. [T1: 問題解決型](#4-t1-問題解決型)
5. [T2: 比較検討型](#5-t2-比較検討型)
6. [T3: 施策提案型](#6-t3-施策提案型)
7. [T4: 業務フロー型](#7-t4-業務フロー型)
8. [コンポーネント定義](#8-コンポーネント定義)

---

## 1. 設計思想

### 原則

- **厳格なJSON定義**: 全ての位置をmm単位で指定
- **ハイブリッド方式**: 基本テンプレート + 再利用コンポーネント
- **セマンティック**: content_keyで動的データをバインド

### レイアウト階層

```
template
├── slide (サイズ・背景)
├── header (タイトル・サブタイトル・日付)
├── body (セクション配置)
│   ├── columns[] (カラム定義)
│   └── sections[] (セクション配置)
└── footer (補足情報)
```

---

## 2. デザイン仕様

### カラーパレット

| 用途 | カラーコード | RGB |
|------|-------------|-----|
| プライマリ（青） | `#2B6CB0` | (43, 108, 176) |
| セカンダリ（グレー） | `#4A5568` | (74, 85, 104) |
| 背景（白） | `#FFFFFF` | (255, 255, 255) |
| 強調背景（薄青） | `#EBF8FF` | (235, 248, 255) |
| 境界線 | `#E2E8F0` | (226, 232, 240) |
| 警告（赤） | `#C53030` | (197, 48, 48) |

### タイポグラフィ

| 要素 | フォント | サイズ | ウェイト |
|------|----------|--------|----------|
| メインタイトル | メイリオ | 28pt | Bold |
| セクション見出し | メイリオ | 18pt | Bold |
| 本文 | メイリオ | 14pt | Regular |
| 注釈・フッター | メイリオ | 10pt | Regular |
| 表ヘッダー | メイリオ | 12pt | Bold |
| 表本文 | メイリオ | 11pt | Regular |

### 余白・グリッド（A3横: 420mm × 297mm）

| 要素 | サイズ |
|------|--------|
| 上余白 | 10mm |
| 下余白 | 10mm |
| 左右余白 | 15mm |
| カラム間隔 | 10mm |
| セクション間隔 | 8mm |
| ヘッダー高さ | 25mm |
| フッター高さ | 12mm |
| 本文エリア高さ | 240mm |
| カラム幅 | 190mm（各） |

---

## 3. テンプレートスキーマ

### 基本構造

```json
{
  "template_id": "T1_problem_solving",
  "template_name": "問題解決型",
  "description": "課題解決の提案に適したテンプレート",
  "slide": {
    "width_mm": 420,
    "height_mm": 297,
    "background_color": "#FFFFFF"
  },
  "header": {
    "height_mm": 25,
    "elements": []
  },
  "body": {
    "margin_top_mm": 35,
    "margin_bottom_mm": 22,
    "columns": 2,
    "column_gap_mm": 10,
    "sections": []
  },
  "footer": {
    "height_mm": 12,
    "elements": []
  },
  "styles": {
    "colors": {},
    "fonts": {}
  }
}
```

### セクション定義

```json
{
  "id": "section_1",
  "name": "現状",
  "column": 0,
  "order": 1,
  "preferred_type": "bullets",
  "min_height_mm": 40,
  "max_height_mm": 80,
  "style": {
    "header_font_size_pt": 18,
    "body_font_size_pt": 14,
    "accent_color": "#2B6CB0"
  }
}
```

---

## 4. T1: 問題解決型

### 用途

課題解決の提案。現状→課題→原因分析→解決策→期待効果の流れ。

### セクション構成

| 位置 | セクション | 推奨タイプ |
|------|-----------|-----------|
| 左上 | 現状 | bullets |
| 左中 | 課題 | bullets |
| 左下 | 原因分析 | table / bullets |
| 右上 | 解決策 | bullets / flowchart |
| 右中 | 実施計画 | table |
| 右下 | 期待効果 | kpi_box / bullets |

### 完全JSON

```json
{
  "template_id": "T1_problem_solving",
  "template_name": "問題解決型",
  "description": "課題解決の提案に適したテンプレート",
  "slide": {
    "width_mm": 420,
    "height_mm": 297,
    "background_color": "#FFFFFF"
  },
  "header": {
    "height_mm": 25,
    "elements": [
      {
        "type": "text",
        "id": "title",
        "x_mm": 15,
        "y_mm": 10,
        "width_mm": 300,
        "height_mm": 15,
        "font_size_pt": 28,
        "font_name": "メイリオ",
        "font_bold": true,
        "font_color": "#1A365D",
        "content_key": "title"
      },
      {
        "type": "text",
        "id": "subtitle",
        "x_mm": 15,
        "y_mm": 26,
        "width_mm": 200,
        "height_mm": 8,
        "font_size_pt": 12,
        "font_color": "#4A5568",
        "content_key": "subtitle"
      },
      {
        "type": "text",
        "id": "date",
        "x_mm": 340,
        "y_mm": 10,
        "width_mm": 65,
        "height_mm": 8,
        "font_size_pt": 10,
        "font_color": "#718096",
        "alignment": "right",
        "content_key": "date"
      }
    ]
  },
  "body": {
    "margin_top_mm": 35,
    "margin_bottom_mm": 22,
    "columns": 2,
    "column_gap_mm": 10,
    "sections": [
      {
        "id": "section_current",
        "name": "現状",
        "column": 0,
        "order": 1,
        "preferred_type": "bullets",
        "min_height_mm": 35,
        "max_height_mm": 70
      },
      {
        "id": "section_issues",
        "name": "課題",
        "column": 0,
        "order": 2,
        "preferred_type": "bullets",
        "min_height_mm": 35,
        "max_height_mm": 70
      },
      {
        "id": "section_causes",
        "name": "原因分析",
        "column": 0,
        "order": 3,
        "preferred_type": "table",
        "min_height_mm": 40,
        "max_height_mm": 80
      },
      {
        "id": "section_solution",
        "name": "解決策",
        "column": 1,
        "order": 1,
        "preferred_type": "bullets",
        "min_height_mm": 40,
        "max_height_mm": 80
      },
      {
        "id": "section_plan",
        "name": "実施計画",
        "column": 1,
        "order": 2,
        "preferred_type": "table",
        "min_height_mm": 35,
        "max_height_mm": 60
      },
      {
        "id": "section_effect",
        "name": "期待効果",
        "column": 1,
        "order": 3,
        "preferred_type": "kpi_box",
        "min_height_mm": 40,
        "max_height_mm": 70
      }
    ]
  },
  "footer": {
    "height_mm": 12,
    "elements": [
      {
        "type": "text",
        "id": "footer_note",
        "x_mm": 15,
        "y_mm": 275,
        "width_mm": 390,
        "height_mm": 10,
        "font_size_pt": 10,
        "font_color": "#718096",
        "content_key": "footer_note"
      }
    ]
  },
  "styles": {
    "colors": {
      "primary": "#2B6CB0",
      "secondary": "#4A5568",
      "accent_bg": "#EBF8FF",
      "border": "#E2E8F0"
    },
    "fonts": {
      "family": "メイリオ"
    }
  }
}
```

---

## 5. T2: 比較検討型

### 用途

選択肢の比較。背景→選択肢A/B/C比較表→推奨案→根拠の流れ。

### セクション構成

| 位置 | セクション | 推奨タイプ |
|------|-----------|-----------|
| 左上 | 背景・目的 | text_block |
| 左中〜下 | 比較表 | table（大型） |
| 右上 | 推奨案 | bullets |
| 右中 | 選定根拠 | bullets |
| 右下 | 次のステップ | flowchart |

### 完全JSON

```json
{
  "template_id": "T2_comparison",
  "template_name": "比較検討型",
  "description": "選択肢の比較に適したテンプレート",
  "slide": {
    "width_mm": 420,
    "height_mm": 297,
    "background_color": "#FFFFFF"
  },
  "header": {
    "height_mm": 25,
    "elements": [
      {
        "type": "text",
        "id": "title",
        "x_mm": 15,
        "y_mm": 10,
        "width_mm": 300,
        "height_mm": 15,
        "font_size_pt": 28,
        "font_bold": true,
        "font_color": "#1A365D",
        "content_key": "title"
      }
    ]
  },
  "body": {
    "margin_top_mm": 35,
    "margin_bottom_mm": 22,
    "columns": 2,
    "column_gap_mm": 10,
    "sections": [
      {
        "id": "section_background",
        "name": "背景・目的",
        "column": 0,
        "order": 1,
        "preferred_type": "text_block",
        "min_height_mm": 30,
        "max_height_mm": 50
      },
      {
        "id": "section_comparison",
        "name": "比較表",
        "column": 0,
        "order": 2,
        "preferred_type": "table",
        "min_height_mm": 80,
        "max_height_mm": 150
      },
      {
        "id": "section_recommendation",
        "name": "推奨案",
        "column": 1,
        "order": 1,
        "preferred_type": "bullets",
        "min_height_mm": 40,
        "max_height_mm": 70
      },
      {
        "id": "section_rationale",
        "name": "選定根拠",
        "column": 1,
        "order": 2,
        "preferred_type": "bullets",
        "min_height_mm": 40,
        "max_height_mm": 70
      },
      {
        "id": "section_next_steps",
        "name": "次のステップ",
        "column": 1,
        "order": 3,
        "preferred_type": "flowchart",
        "min_height_mm": 40,
        "max_height_mm": 60
      }
    ]
  },
  "footer": {
    "height_mm": 12,
    "elements": []
  },
  "styles": {
    "colors": {
      "primary": "#2B6CB0",
      "secondary": "#4A5568"
    }
  }
}
```

---

## 6. T3: 施策提案型

### 用途

新規施策の説明。背景→目的→施策概要→スケジュール→予算の流れ。

### セクション構成

| 位置 | セクション | 推奨タイプ |
|------|-----------|-----------|
| 左上 | 背景 | text_block |
| 左中 | 目的 | bullets |
| 左下 | 対象範囲 | bullets |
| 右上 | 施策概要 | bullets |
| 右中 | スケジュール | table / flowchart |
| 右下 | 予算・リソース | table / kpi_box |

### 完全JSON

```json
{
  "template_id": "T3_policy_proposal",
  "template_name": "施策提案型",
  "description": "新規施策の説明に適したテンプレート",
  "slide": {
    "width_mm": 420,
    "height_mm": 297,
    "background_color": "#FFFFFF"
  },
  "header": {
    "height_mm": 25,
    "elements": [
      {
        "type": "text",
        "id": "title",
        "x_mm": 15,
        "y_mm": 10,
        "width_mm": 300,
        "height_mm": 15,
        "font_size_pt": 28,
        "font_bold": true,
        "font_color": "#1A365D",
        "content_key": "title"
      }
    ]
  },
  "body": {
    "margin_top_mm": 35,
    "margin_bottom_mm": 22,
    "columns": 2,
    "column_gap_mm": 10,
    "sections": [
      {
        "id": "section_background",
        "name": "背景",
        "column": 0,
        "order": 1,
        "preferred_type": "text_block",
        "min_height_mm": 35,
        "max_height_mm": 60
      },
      {
        "id": "section_purpose",
        "name": "目的",
        "column": 0,
        "order": 2,
        "preferred_type": "bullets",
        "min_height_mm": 35,
        "max_height_mm": 60
      },
      {
        "id": "section_scope",
        "name": "対象範囲",
        "column": 0,
        "order": 3,
        "preferred_type": "bullets",
        "min_height_mm": 35,
        "max_height_mm": 60
      },
      {
        "id": "section_overview",
        "name": "施策概要",
        "column": 1,
        "order": 1,
        "preferred_type": "bullets",
        "min_height_mm": 50,
        "max_height_mm": 90
      },
      {
        "id": "section_schedule",
        "name": "スケジュール",
        "column": 1,
        "order": 2,
        "preferred_type": "table",
        "min_height_mm": 40,
        "max_height_mm": 70
      },
      {
        "id": "section_budget",
        "name": "予算・リソース",
        "column": 1,
        "order": 3,
        "preferred_type": "table",
        "min_height_mm": 35,
        "max_height_mm": 55
      }
    ]
  },
  "footer": {
    "height_mm": 12,
    "elements": []
  },
  "styles": {
    "colors": {
      "primary": "#2B6CB0"
    }
  }
}
```

---

## 7. T4: 業務フロー型

### 用途

プロセス改善。現状フロー→課題→改善後フロー→効果の流れ。

### セクション構成

| 位置 | セクション | 推奨タイプ |
|------|-----------|-----------|
| 左上 | 現状フロー | flowchart（縦） |
| 左下 | 課題点 | bullets |
| 右上 | 改善後フロー | flowchart（縦） |
| 右下 | 改善効果 | kpi_box / bullets |

### 完全JSON

```json
{
  "template_id": "T4_workflow",
  "template_name": "業務フロー型",
  "description": "プロセス改善に適したテンプレート",
  "slide": {
    "width_mm": 420,
    "height_mm": 297,
    "background_color": "#FFFFFF"
  },
  "header": {
    "height_mm": 25,
    "elements": [
      {
        "type": "text",
        "id": "title",
        "x_mm": 15,
        "y_mm": 10,
        "width_mm": 300,
        "height_mm": 15,
        "font_size_pt": 28,
        "font_bold": true,
        "font_color": "#1A365D",
        "content_key": "title"
      }
    ]
  },
  "body": {
    "margin_top_mm": 35,
    "margin_bottom_mm": 22,
    "columns": 2,
    "column_gap_mm": 10,
    "sections": [
      {
        "id": "section_current_flow",
        "name": "現状フロー",
        "column": 0,
        "order": 1,
        "preferred_type": "flowchart",
        "preferred_direction": "v",
        "min_height_mm": 100,
        "max_height_mm": 150
      },
      {
        "id": "section_issues",
        "name": "課題点",
        "column": 0,
        "order": 2,
        "preferred_type": "bullets",
        "min_height_mm": 40,
        "max_height_mm": 70
      },
      {
        "id": "section_improved_flow",
        "name": "改善後フロー",
        "column": 1,
        "order": 1,
        "preferred_type": "flowchart",
        "preferred_direction": "v",
        "min_height_mm": 100,
        "max_height_mm": 150
      },
      {
        "id": "section_effect",
        "name": "改善効果",
        "column": 1,
        "order": 2,
        "preferred_type": "kpi_box",
        "min_height_mm": 40,
        "max_height_mm": 70
      }
    ]
  },
  "footer": {
    "height_mm": 12,
    "elements": []
  },
  "styles": {
    "colors": {
      "primary": "#2B6CB0",
      "current_flow": "#718096",
      "improved_flow": "#38A169"
    }
  }
}
```

---

## 8. コンポーネント定義

### components/bullets.json

```json
{
  "component_id": "bullets",
  "name": "箇条書き",
  "description": "要点リスト表示",
  "default_style": {
    "bullet_char": "・",
    "indent_mm": 5,
    "line_spacing_mm": 8,
    "font_size_pt": 14,
    "font_color": "#4A5568"
  },
  "content_schema": {
    "type": "object",
    "properties": {
      "items": {
        "type": "array",
        "items": {
          "type": "string",
          "maxLength": 50
        },
        "maxItems": 8
      }
    }
  }
}
```

### components/table.json

```json
{
  "component_id": "table",
  "name": "表・マトリックス",
  "description": "比較・一覧表示",
  "default_style": {
    "header_bg_color": "#2B6CB0",
    "header_font_color": "#FFFFFF",
    "header_font_size_pt": 12,
    "body_font_size_pt": 11,
    "row_height_mm": 8,
    "alternate_row_color": "#EBF8FF",
    "border_color": "#E2E8F0"
  },
  "content_schema": {
    "type": "object",
    "properties": {
      "columns": {
        "type": "array",
        "items": {"type": "string"},
        "maxItems": 5
      },
      "rows": {
        "type": "array",
        "items": {
          "type": "array",
          "items": {"type": "string"}
        },
        "maxItems": 10
      }
    }
  }
}
```

### components/flowchart.json

```json
{
  "component_id": "flowchart",
  "name": "フローチャート",
  "description": "プロセス・手順表示",
  "default_style": {
    "step_bg_color": "#EBF8FF",
    "step_border_color": "#2B6CB0",
    "arrow_color": "#2B6CB0",
    "font_size_pt": 12,
    "step_padding_mm": 5
  },
  "content_schema": {
    "type": "object",
    "properties": {
      "steps": {
        "type": "array",
        "items": {"type": "string", "maxLength": 30},
        "maxItems": 5
      },
      "direction": {
        "type": "string",
        "enum": ["h", "v"],
        "default": "h"
      }
    }
  }
}
```

---

## テンプレート追加手順

1. `templates/`に新規JSONファイルを作成
2. 基本スキーマに従いセクションを定義
3. `layout_engine.py`のテンプレート読み込みに追加
4. AIプロンプトのテンプレート選択肢に追加
