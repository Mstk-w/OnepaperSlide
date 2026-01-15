# Layout-Agent: JSONレイアウトエンジン実装ガイド

## 担当ファイル

- `src/layout_engine.py` - レイアウト計算エンジン

## 目次

1. [設計思想](#1-設計思想)
2. [単位変換](#2-単位変換)
3. [グリッドシステム](#3-グリッドシステム)
4. [セクション配置](#4-セクション配置)
5. [コンポーネント配置](#5-コンポーネント配置)
6. [完全実装例](#6-完全実装例)

---

## 1. 設計思想

### 原則

- **厳格な座標指定**: 全ての図形位置をmm単位で指定し、文字ズレ・図形被りを防止
- **ハイブリッド方式**: 4つの基本テンプレート + 再利用可能な部品（コンポーネント）
- **Auto-Shrink対応**: テキスト溢れ時の自動フォント縮小

### データフロー

```
AI生成JSON → process_layout() → 座標付きレイアウトデータ → PPTX Builder
```

---

## 2. 単位変換

python-pptxはEMU（English Metric Units）を使用。mm→EMU変換が必要。

```python
from pptx.util import Mm, Pt, Emu

# 定数定義
class Units:
    """単位変換ユーティリティ"""

    # A3横サイズ
    SLIDE_WIDTH_MM = 420
    SLIDE_HEIGHT_MM = 297

    # EMU変換係数
    EMU_PER_MM = 36000

    @staticmethod
    def mm_to_emu(mm: float) -> int:
        """ミリメートルをEMUに変換"""
        return int(mm * Units.EMU_PER_MM)

    @staticmethod
    def pt_to_emu(pt: float) -> int:
        """ポイントをEMUに変換（フォントサイズ用）"""
        return int(pt * 12700)

    @staticmethod
    def mm(value: float):
        """python-pptx互換のMmラッパー"""
        return Mm(value)
```

### 使用例

```python
# 座標指定
x = Units.mm(15)  # 左から15mm
y = Units.mm(25)  # 上から25mm
width = Units.mm(190)  # 幅190mm
height = Units.mm(120)  # 高さ120mm
```

---

## 3. グリッドシステム

### A3横レイアウト定数

```python
class LayoutConstants:
    """レイアウト定数（A3横: 420mm × 297mm）"""

    # スライドサイズ
    SLIDE_WIDTH = 420   # mm
    SLIDE_HEIGHT = 297  # mm

    # 余白
    MARGIN_TOP = 10     # mm
    MARGIN_BOTTOM = 10  # mm
    MARGIN_LEFT = 15    # mm
    MARGIN_RIGHT = 15   # mm

    # ヘッダー・フッター
    HEADER_HEIGHT = 25  # mm
    FOOTER_HEIGHT = 12  # mm

    # カラム設定
    COLUMN_GAP = 10     # mm
    COLUMN_COUNT = 2

    # セクション間隔
    SECTION_GAP = 8     # mm

    @classmethod
    def content_width(cls) -> float:
        """コンテンツ領域の幅"""
        return cls.SLIDE_WIDTH - cls.MARGIN_LEFT - cls.MARGIN_RIGHT

    @classmethod
    def content_height(cls) -> float:
        """コンテンツ領域の高さ（本文エリア）"""
        return (cls.SLIDE_HEIGHT
                - cls.MARGIN_TOP
                - cls.MARGIN_BOTTOM
                - cls.HEADER_HEIGHT
                - cls.FOOTER_HEIGHT)

    @classmethod
    def column_width(cls) -> float:
        """1カラムの幅"""
        total_gap = cls.COLUMN_GAP * (cls.COLUMN_COUNT - 1)
        return (cls.content_width() - total_gap) / cls.COLUMN_COUNT
```

### グリッド計算

```python
def calculate_grid() -> dict:
    """グリッド座標を計算"""
    lc = LayoutConstants

    return {
        "header": {
            "x": lc.MARGIN_LEFT,
            "y": lc.MARGIN_TOP,
            "width": lc.content_width(),
            "height": lc.HEADER_HEIGHT
        },
        "body": {
            "x": lc.MARGIN_LEFT,
            "y": lc.MARGIN_TOP + lc.HEADER_HEIGHT,
            "width": lc.content_width(),
            "height": lc.content_height()
        },
        "footer": {
            "x": lc.MARGIN_LEFT,
            "y": lc.SLIDE_HEIGHT - lc.MARGIN_BOTTOM - lc.FOOTER_HEIGHT,
            "width": lc.content_width(),
            "height": lc.FOOTER_HEIGHT
        },
        "columns": [
            {
                "x": lc.MARGIN_LEFT,
                "y": lc.MARGIN_TOP + lc.HEADER_HEIGHT,
                "width": lc.column_width(),
                "height": lc.content_height()
            },
            {
                "x": lc.MARGIN_LEFT + lc.column_width() + lc.COLUMN_GAP,
                "y": lc.MARGIN_TOP + lc.HEADER_HEIGHT,
                "width": lc.column_width(),
                "height": lc.content_height()
            }
        ]
    }
```

---

## 4. セクション配置

### 配置アルゴリズム

```python
from dataclasses import dataclass
from typing import List

@dataclass
class SectionPlacement:
    """セクションの配置情報"""
    section_id: str
    column: int
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float

def distribute_sections(
    sections: List[dict],
    template_layout: dict
) -> List[SectionPlacement]:
    """セクションを2カラムに分配"""
    lc = LayoutConstants
    grid = calculate_grid()

    placements = []

    # カラムごとの現在Y位置を追跡
    column_y = [
        grid["columns"][0]["y"],
        grid["columns"][1]["y"]
    ]

    for section in sections:
        col_idx = section.get("column", 0)

        # セクション高さの推定
        estimated_height = estimate_section_height(section)

        placement = SectionPlacement(
            section_id=section["id"],
            column=col_idx,
            x_mm=grid["columns"][col_idx]["x"],
            y_mm=column_y[col_idx],
            width_mm=lc.column_width(),
            height_mm=estimated_height
        )

        placements.append(placement)

        # Y位置を更新（次のセクション用）
        column_y[col_idx] += estimated_height + lc.SECTION_GAP

    return placements

def estimate_section_height(section: dict) -> float:
    """セクションの高さを推定"""
    section_type = section.get("type", "text_block")

    # ヘッダー高さ（常に含む）
    header_height = 10  # mm

    content = section.get("content", {})

    if section_type == "bullets":
        items = content.get("items", [])
        # 1項目あたり約8mm
        return header_height + len(items) * 8 + 5

    elif section_type == "table":
        rows = content.get("rows", [])
        # ヘッダー行 + データ行
        return header_height + (len(rows) + 1) * 8 + 5

    elif section_type == "flowchart":
        steps = content.get("steps", [])
        direction = content.get("direction", "h")
        if direction == "h":
            return header_height + 40  # 横フローは固定高さ
        else:
            return header_height + len(steps) * 25 + 5

    elif section_type == "kpi_box":
        return header_height + 35

    else:  # text_block
        text = content.get("text", "")
        # 1行あたり約6mm、1行40文字程度
        lines = max(1, len(text) // 40 + 1)
        return header_height + lines * 6 + 5
```

---

## 5. コンポーネント配置

### 箇条書き（bullets）

```python
def layout_bullets(
    section: dict,
    placement: SectionPlacement
) -> dict:
    """箇条書きコンポーネントのレイアウト"""
    content = section.get("content", {})
    items = content.get("items", [])

    bullet_layouts = []
    y_offset = 10  # ヘッダー分のオフセット

    for i, item in enumerate(items):
        bullet_layouts.append({
            "text": item,
            "x_mm": placement.x_mm + 5,  # インデント
            "y_mm": placement.y_mm + y_offset + i * 8,
            "width_mm": placement.width_mm - 10,
            "height_mm": 7,
            "indent_level": item.get("indent", 0) if isinstance(item, dict) else 0
        })

    return {
        "type": "bullets",
        "header": {
            "text": section.get("header", ""),
            "x_mm": placement.x_mm,
            "y_mm": placement.y_mm,
            "width_mm": placement.width_mm,
            "height_mm": 10
        },
        "items": bullet_layouts
    }
```

### 表（table）

```python
def layout_table(
    section: dict,
    placement: SectionPlacement
) -> dict:
    """表コンポーネントのレイアウト"""
    content = section.get("content", {})
    columns = content.get("columns", [])
    rows = content.get("rows", [])

    col_count = len(columns)
    row_count = len(rows) + 1  # ヘッダー行含む

    # セル寸法計算
    table_width = placement.width_mm - 4
    table_height = row_count * 8
    col_width = table_width / col_count
    row_height = 8

    return {
        "type": "table",
        "header": {
            "text": section.get("header", ""),
            "x_mm": placement.x_mm,
            "y_mm": placement.y_mm,
            "width_mm": placement.width_mm,
            "height_mm": 10
        },
        "table": {
            "x_mm": placement.x_mm + 2,
            "y_mm": placement.y_mm + 10,
            "width_mm": table_width,
            "height_mm": table_height,
            "columns": columns,
            "rows": rows,
            "col_width_mm": col_width,
            "row_height_mm": row_height
        }
    }
```

### フローチャート（flowchart）

```python
def layout_flowchart(
    section: dict,
    placement: SectionPlacement
) -> dict:
    """フローチャートコンポーネントのレイアウト"""
    content = section.get("content", {})
    steps = content.get("steps", [])
    direction = content.get("direction", "h")  # h: 横, v: 縦

    step_layouts = []
    step_count = len(steps)

    if direction == "h":
        # 横配置
        step_width = (placement.width_mm - 10) / step_count - 5
        step_height = 25

        for i, step in enumerate(steps):
            x = placement.x_mm + 5 + i * (step_width + 5)
            step_layouts.append({
                "text": step,
                "x_mm": x,
                "y_mm": placement.y_mm + 12,
                "width_mm": step_width,
                "height_mm": step_height,
                "show_arrow": i < step_count - 1
            })
    else:
        # 縦配置
        step_width = placement.width_mm - 20
        step_height = 18

        for i, step in enumerate(steps):
            y = placement.y_mm + 12 + i * (step_height + 7)
            step_layouts.append({
                "text": step,
                "x_mm": placement.x_mm + 10,
                "y_mm": y,
                "width_mm": step_width,
                "height_mm": step_height,
                "show_arrow": i < step_count - 1
            })

    return {
        "type": "flowchart",
        "header": {
            "text": section.get("header", ""),
            "x_mm": placement.x_mm,
            "y_mm": placement.y_mm,
            "width_mm": placement.width_mm,
            "height_mm": 10
        },
        "direction": direction,
        "steps": step_layouts
    }
```

---

## 6. 完全実装例

### layout_engine.py

```python
"""
OnePaperSlide レイアウトエンジン
JSON構造化データを座標付きレイアウトデータに変換
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import json
from pathlib import Path


class LayoutConstants:
    """レイアウト定数（A3横: 420mm × 297mm）"""
    SLIDE_WIDTH = 420
    SLIDE_HEIGHT = 297
    MARGIN_TOP = 10
    MARGIN_BOTTOM = 10
    MARGIN_LEFT = 15
    MARGIN_RIGHT = 15
    HEADER_HEIGHT = 25
    FOOTER_HEIGHT = 12
    COLUMN_GAP = 10
    COLUMN_COUNT = 2
    SECTION_GAP = 8

    @classmethod
    def content_width(cls) -> float:
        return cls.SLIDE_WIDTH - cls.MARGIN_LEFT - cls.MARGIN_RIGHT

    @classmethod
    def content_height(cls) -> float:
        return (cls.SLIDE_HEIGHT - cls.MARGIN_TOP - cls.MARGIN_BOTTOM
                - cls.HEADER_HEIGHT - cls.FOOTER_HEIGHT)

    @classmethod
    def column_width(cls) -> float:
        total_gap = cls.COLUMN_GAP * (cls.COLUMN_COUNT - 1)
        return (cls.content_width() - total_gap) / cls.COLUMN_COUNT


@dataclass
class ElementLayout:
    """要素のレイアウト情報"""
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float


def load_template(template_id: str) -> dict:
    """テンプレートJSONを読み込み"""
    template_path = Path(__file__).parent.parent / "templates" / f"{template_id}.json"
    with open(template_path, encoding="utf-8") as f:
        return json.load(f)


def process_layout(ai_output: dict) -> dict:
    """
    AI出力を座標付きレイアウトデータに変換

    Args:
        ai_output: AI生成の構造化データ

    Returns:
        座標情報を含むレイアウトデータ
    """
    lc = LayoutConstants
    template_id = ai_output.get("recommended_template", "T1_problem_solving")

    # テンプレート読み込み
    template = load_template(template_id)

    # グリッド計算
    grid = calculate_grid()

    # ヘッダーレイアウト
    header_layout = {
        "title": {
            "text": ai_output.get("title", "無題"),
            **grid["header"],
            "font_size_pt": 28,
            "font_bold": True
        },
        "subtitle": {
            "text": ai_output.get("subtitle", ""),
            "x_mm": lc.MARGIN_LEFT,
            "y_mm": lc.MARGIN_TOP + 18,
            "width_mm": lc.content_width(),
            "height_mm": 7,
            "font_size_pt": 14
        }
    }

    # セクション配置
    sections = ai_output.get("sections", [])
    section_placements = distribute_sections(sections, template)

    # 各セクションのレイアウト計算
    section_layouts = []
    for section, placement in zip(sections, section_placements):
        section_type = section.get("type", "text_block")

        if section_type == "bullets":
            layout = layout_bullets(section, placement)
        elif section_type == "table":
            layout = layout_table(section, placement)
        elif section_type == "flowchart":
            layout = layout_flowchart(section, placement)
        elif section_type == "kpi_box":
            layout = layout_kpi_box(section, placement)
        else:
            layout = layout_text_block(section, placement)

        section_layouts.append(layout)

    # フッターレイアウト
    footer_layout = {
        "text": ai_output.get("footer_note", ""),
        **grid["footer"],
        "font_size_pt": 10
    }

    return {
        "template_id": template_id,
        "slide": {
            "width_mm": lc.SLIDE_WIDTH,
            "height_mm": lc.SLIDE_HEIGHT
        },
        "header": header_layout,
        "sections": section_layouts,
        "footer": footer_layout
    }


def layout_text_block(section: dict, placement) -> dict:
    """テキストブロックのレイアウト"""
    content = section.get("content", {})
    text = content.get("text", "") if isinstance(content, dict) else str(content)

    return {
        "type": "text_block",
        "header": {
            "text": section.get("header", ""),
            "x_mm": placement.x_mm,
            "y_mm": placement.y_mm,
            "width_mm": placement.width_mm,
            "height_mm": 10
        },
        "body": {
            "text": text,
            "x_mm": placement.x_mm + 2,
            "y_mm": placement.y_mm + 10,
            "width_mm": placement.width_mm - 4,
            "height_mm": placement.height_mm - 12
        }
    }


def layout_kpi_box(section: dict, placement) -> dict:
    """KPIボックスのレイアウト"""
    content = section.get("content", {})

    return {
        "type": "kpi_box",
        "header": {
            "text": section.get("header", ""),
            "x_mm": placement.x_mm,
            "y_mm": placement.y_mm,
            "width_mm": placement.width_mm,
            "height_mm": 10
        },
        "value": {
            "text": str(content.get("value", "")),
            "x_mm": placement.x_mm + 5,
            "y_mm": placement.y_mm + 12,
            "width_mm": placement.width_mm - 10,
            "height_mm": 20,
            "font_size_pt": 32,
            "font_bold": True
        },
        "unit": content.get("unit", ""),
        "label": content.get("label", "")
    }
```

---

## エラー防止チェックリスト

- [ ] 全ての座標がスライド範囲内に収まっているか
- [ ] セクションが重ならないか
- [ ] カラム間のギャップが正しいか
- [ ] フォントサイズがボックスサイズに対して適切か
- [ ] 余白が統一されているか
