# PPTX-Agent: python-pptx実装ガイド

## 担当ファイル

- `src/pptx_builder.py` - PPTX生成モジュール

## 目次

1. [基本操作](#1-基本操作)
2. [A3横スライド生成](#2-a3横スライド生成)
3. [テキストボックス](#3-テキストボックス)
4. [図形描画](#4-図形描画)
5. [表生成](#5-表生成)
6. [フローチャート](#6-フローチャート)
7. [Auto-Shrink実装](#7-auto-shrink実装)
8. [完全実装例](#8-完全実装例)

---

## 1. 基本操作

### インポートと初期化

```python
from pptx import Presentation
from pptx.util import Mm, Pt, Emu
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RgbColor
from pptx.enum.dml import MSO_THEME_COLOR
from io import BytesIO
```

### カラーパレット

```python
class Colors:
    """デザイン仕様に基づくカラーパレット"""
    PRIMARY = RgbColor(0x2B, 0x6C, 0xB0)      # 青 - 見出し・アクセント
    SECONDARY = RgbColor(0x4A, 0x55, 0x68)    # グレー - 本文
    BACKGROUND = RgbColor(0xFF, 0xFF, 0xFF)   # 白
    ACCENT_BG = RgbColor(0xEB, 0xF8, 0xFF)    # 薄い青 - ボックス背景
    BORDER = RgbColor(0xE2, 0xE8, 0xF0)       # 薄いグレー - 境界線
    ALERT = RgbColor(0xC5, 0x30, 0x30)        # 赤 - 警告

    @staticmethod
    def from_hex(hex_color: str) -> RgbColor:
        """16進数文字列からRgbColorを生成"""
        hex_color = hex_color.lstrip("#")
        return RgbColor(
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )
```

### フォント設定

```python
class Fonts:
    """タイポグラフィ設定"""
    FAMILY = "メイリオ"

    # サイズ（ポイント）
    TITLE = 28
    SECTION_HEADER = 18
    BODY = 14
    FOOTER = 10
    TABLE_HEADER = 12
    TABLE_BODY = 11
```

---

## 2. A3横スライド生成

```python
def create_a3_presentation() -> Presentation:
    """A3横サイズのプレゼンテーションを作成"""
    prs = Presentation()

    # A3横: 420mm × 297mm
    prs.slide_width = Mm(420)
    prs.slide_height = Mm(297)

    return prs

def add_blank_slide(prs: Presentation):
    """空白スライドを追加"""
    # 空白レイアウトを取得（インデックス6が一般的）
    blank_layout = prs.slide_layouts[6]
    return prs.slides.add_slide(blank_layout)
```

---

## 3. テキストボックス

### 基本テキストボックス

```python
def add_text_box(
    slide,
    text: str,
    x_mm: float,
    y_mm: float,
    width_mm: float,
    height_mm: float,
    font_size_pt: int = Fonts.BODY,
    font_bold: bool = False,
    font_color: RgbColor = Colors.SECONDARY,
    alignment: PP_ALIGN = PP_ALIGN.LEFT
):
    """テキストボックスを追加"""
    shape = slide.shapes.add_textbox(
        Mm(x_mm), Mm(y_mm),
        Mm(width_mm), Mm(height_mm)
    )

    tf = shape.text_frame
    tf.word_wrap = True
    tf.auto_size = None  # 自動サイズ調整を無効化

    p = tf.paragraphs[0]
    p.text = text
    p.font.name = Fonts.FAMILY
    p.font.size = Pt(font_size_pt)
    p.font.bold = font_bold
    p.font.color.rgb = font_color
    p.alignment = alignment

    return shape
```

### セクションヘッダー

```python
def add_section_header(
    slide,
    text: str,
    x_mm: float,
    y_mm: float,
    width_mm: float
):
    """セクション見出しを追加（アクセントバー付き）"""
    # アクセントバー（左端の青い縦線）
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Mm(x_mm), Mm(y_mm),
        Mm(3), Mm(8)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = Colors.PRIMARY
    bar.line.fill.background()  # 枠線なし

    # 見出しテキスト
    add_text_box(
        slide,
        text,
        x_mm + 5,
        y_mm,
        width_mm - 5,
        10,
        font_size_pt=Fonts.SECTION_HEADER,
        font_bold=True,
        font_color=Colors.PRIMARY
    )
```

### 箇条書き

```python
def add_bullet_list(
    slide,
    items: list,
    x_mm: float,
    y_mm: float,
    width_mm: float,
    height_mm: float
):
    """箇条書きリストを追加"""
    shape = slide.shapes.add_textbox(
        Mm(x_mm), Mm(y_mm),
        Mm(width_mm), Mm(height_mm)
    )

    tf = shape.text_frame
    tf.word_wrap = True

    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()

        # 箇条書き記号を手動で追加
        text = item if isinstance(item, str) else item.get("text", "")
        indent = item.get("indent", 0) if isinstance(item, dict) else 0

        p.text = "・" + text if indent == 0 else "  ・" + text
        p.font.name = Fonts.FAMILY
        p.font.size = Pt(Fonts.BODY)
        p.font.color.rgb = Colors.SECONDARY
        p.space_after = Pt(4)
```

---

## 4. 図形描画

### 矩形ボックス（背景付き）

```python
def add_box_with_background(
    slide,
    x_mm: float,
    y_mm: float,
    width_mm: float,
    height_mm: float,
    fill_color: RgbColor = Colors.ACCENT_BG,
    border_color: RgbColor = Colors.BORDER,
    corner_radius_mm: float = 2
):
    """角丸矩形ボックスを追加"""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Mm(x_mm), Mm(y_mm),
        Mm(width_mm), Mm(height_mm)
    )

    # 塗りつぶし
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color

    # 枠線
    shape.line.color.rgb = border_color
    shape.line.width = Pt(0.5)

    # 角丸の調整
    if hasattr(shape, 'adjustments') and len(shape.adjustments) > 0:
        # 角丸の半径を設定（0-1の範囲で指定）
        shape.adjustments[0] = corner_radius_mm / min(width_mm, height_mm)

    return shape
```

### 矢印

```python
def add_arrow(
    slide,
    start_x_mm: float,
    start_y_mm: float,
    end_x_mm: float,
    end_y_mm: float,
    color: RgbColor = Colors.PRIMARY
):
    """矢印を追加"""
    from pptx.enum.shapes import MSO_CONNECTOR

    # コネクタとして矢印を追加
    connector = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Mm(start_x_mm), Mm(start_y_mm),
        Mm(end_x_mm), Mm(end_y_mm)
    )

    connector.line.color.rgb = color
    connector.line.width = Pt(1.5)

    # 終点に矢印を設定
    from pptx.enum.shapes import MSO_CONNECTOR_TYPE
    connector.line.dash_style = None

    return connector
```

### 三角矢印（図形）

```python
def add_triangle_arrow(
    slide,
    x_mm: float,
    y_mm: float,
    direction: str = "right"  # right, down, left, up
):
    """三角形の矢印を追加"""
    size_mm = 8

    if direction == "right":
        rotation = 90
    elif direction == "down":
        rotation = 180
    elif direction == "left":
        rotation = 270
    else:  # up
        rotation = 0

    shape = slide.shapes.add_shape(
        MSO_SHAPE.ISOSCELES_TRIANGLE,
        Mm(x_mm), Mm(y_mm),
        Mm(size_mm), Mm(size_mm)
    )

    shape.rotation = rotation
    shape.fill.solid()
    shape.fill.fore_color.rgb = Colors.PRIMARY
    shape.line.fill.background()

    return shape
```

---

## 5. 表生成

```python
def add_table(
    slide,
    x_mm: float,
    y_mm: float,
    width_mm: float,
    columns: list,
    rows: list
):
    """表を追加"""
    row_count = len(rows) + 1  # ヘッダー行含む
    col_count = len(columns)

    # 行高さ計算
    row_height = Mm(8)

    # 表を追加
    table = slide.shapes.add_table(
        row_count, col_count,
        Mm(x_mm), Mm(y_mm),
        Mm(width_mm), row_height * row_count
    ).table

    # 列幅を均等に設定
    col_width = Mm(width_mm / col_count)
    for col in table.columns:
        col.width = col_width

    # ヘッダー行
    for i, col_name in enumerate(columns):
        cell = table.cell(0, i)
        cell.text = col_name
        cell.fill.solid()
        cell.fill.fore_color.rgb = Colors.PRIMARY

        # テキスト書式
        p = cell.text_frame.paragraphs[0]
        p.font.name = Fonts.FAMILY
        p.font.size = Pt(Fonts.TABLE_HEADER)
        p.font.bold = True
        p.font.color.rgb = RgbColor(0xFF, 0xFF, 0xFF)  # 白
        p.alignment = PP_ALIGN.CENTER

        # 垂直中央揃え
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE

    # データ行
    for row_idx, row_data in enumerate(rows):
        for col_idx, cell_value in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = str(cell_value)

            # 交互背景色
            if row_idx % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = Colors.ACCENT_BG
            else:
                cell.fill.background()

            # テキスト書式
            p = cell.text_frame.paragraphs[0]
            p.font.name = Fonts.FAMILY
            p.font.size = Pt(Fonts.TABLE_BODY)
            p.font.color.rgb = Colors.SECONDARY
            p.alignment = PP_ALIGN.LEFT

            cell.vertical_anchor = MSO_ANCHOR.MIDDLE

    return table
```

---

## 6. フローチャート

```python
def add_flowchart(
    slide,
    steps: list,
    x_mm: float,
    y_mm: float,
    width_mm: float,
    direction: str = "h"  # h: 横, v: 縦
):
    """フローチャートを追加"""
    step_count = len(steps)

    if direction == "h":
        # 横配置
        step_width = (width_mm - (step_count - 1) * 15) / step_count
        step_height = 25

        for i, step in enumerate(steps):
            step_x = x_mm + i * (step_width + 15)

            # ステップボックス
            box = add_box_with_background(
                slide,
                step_x, y_mm,
                step_width, step_height,
                fill_color=Colors.ACCENT_BG if i % 2 == 0 else Colors.BACKGROUND
            )

            # ステップテキスト
            add_text_box(
                slide,
                step.get("text", step) if isinstance(step, dict) else step,
                step_x + 2, y_mm + 2,
                step_width - 4, step_height - 4,
                font_size_pt=12,
                alignment=PP_ALIGN.CENTER
            )

            # 矢印（最後以外）
            if i < step_count - 1:
                arrow_x = step_x + step_width + 3
                arrow_y = y_mm + step_height / 2 - 4
                add_triangle_arrow(slide, arrow_x, arrow_y, "right")

    else:
        # 縦配置
        step_width = width_mm - 20
        step_height = 18

        for i, step in enumerate(steps):
            step_y = y_mm + i * (step_height + 12)

            # ステップボックス
            add_box_with_background(
                slide,
                x_mm + 10, step_y,
                step_width, step_height
            )

            # ステップテキスト
            add_text_box(
                slide,
                step.get("text", step) if isinstance(step, dict) else step,
                x_mm + 12, step_y + 2,
                step_width - 4, step_height - 4,
                font_size_pt=12,
                alignment=PP_ALIGN.CENTER
            )

            # 矢印（最後以外）
            if i < step_count - 1:
                arrow_x = x_mm + 10 + step_width / 2 - 4
                arrow_y = step_y + step_height + 2
                add_triangle_arrow(slide, arrow_x, arrow_y, "down")
```

---

## 7. Auto-Shrink実装

```python
def auto_shrink_text(
    text: str,
    box_width_mm: float,
    box_height_mm: float,
    initial_font_size_pt: int,
    min_font_size_pt: int = 8
) -> int:
    """
    テキストがボックスに収まるフォントサイズを計算

    簡易推定: 1ptあたり約0.35mmの文字幅、行高さは1.2倍
    """
    font_size = initial_font_size_pt

    while font_size >= min_font_size_pt:
        # 1文字あたりの幅（mm）
        char_width_mm = font_size * 0.35

        # 1行あたりの文字数
        chars_per_line = int(box_width_mm / char_width_mm)

        # 必要な行数
        text_length = len(text)
        required_lines = (text_length + chars_per_line - 1) // chars_per_line

        # 行高さ（mm）
        line_height_mm = font_size * 0.35 * 1.2

        # 必要な高さ
        required_height = required_lines * line_height_mm

        if required_height <= box_height_mm:
            return font_size

        font_size -= 1

    return min_font_size_pt


def add_text_box_with_auto_shrink(
    slide,
    text: str,
    x_mm: float,
    y_mm: float,
    width_mm: float,
    height_mm: float,
    initial_font_size_pt: int = Fonts.BODY,
    min_font_size_pt: int = 8,
    **kwargs
):
    """Auto-Shrink付きテキストボックス"""
    font_size = auto_shrink_text(
        text, width_mm, height_mm,
        initial_font_size_pt, min_font_size_pt
    )

    return add_text_box(
        slide, text,
        x_mm, y_mm, width_mm, height_mm,
        font_size_pt=font_size,
        **kwargs
    )
```

---

## 8. 完全実装例

### pptx_builder.py

```python
"""
OnePaperSlide PPTX生成モジュール
レイアウトデータからPowerPointファイルを生成
"""

from pptx import Presentation
from pptx.util import Mm, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RgbColor
from io import BytesIO
from typing import Dict, Any


class Colors:
    PRIMARY = RgbColor(0x2B, 0x6C, 0xB0)
    SECONDARY = RgbColor(0x4A, 0x55, 0x68)
    BACKGROUND = RgbColor(0xFF, 0xFF, 0xFF)
    ACCENT_BG = RgbColor(0xEB, 0xF8, 0xFF)
    BORDER = RgbColor(0xE2, 0xE8, 0xF0)


class Fonts:
    FAMILY = "メイリオ"
    TITLE = 28
    SECTION_HEADER = 18
    BODY = 14
    FOOTER = 10


def build_pptx(layout_data: Dict[str, Any]) -> bytes:
    """
    レイアウトデータからPPTXを生成

    Args:
        layout_data: 座標情報を含むレイアウトデータ

    Returns:
        PPTXファイルのバイト列
    """
    # プレゼンテーション作成
    prs = Presentation()
    prs.slide_width = Mm(layout_data["slide"]["width_mm"])
    prs.slide_height = Mm(layout_data["slide"]["height_mm"])

    # 空白スライドを追加
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # ヘッダー描画
    render_header(slide, layout_data["header"])

    # セクション描画
    for section in layout_data["sections"]:
        render_section(slide, section)

    # フッター描画
    render_footer(slide, layout_data["footer"])

    # バイト列として出力
    output = BytesIO()
    prs.save(output)
    output.seek(0)

    return output.read()


def render_header(slide, header_data: dict):
    """ヘッダーを描画"""
    title = header_data.get("title", {})
    add_text_box(
        slide,
        title.get("text", ""),
        title.get("x_mm", 15),
        title.get("y_mm", 10),
        title.get("width_mm", 390),
        title.get("height_mm", 15),
        font_size_pt=title.get("font_size_pt", Fonts.TITLE),
        font_bold=title.get("font_bold", True),
        font_color=Colors.PRIMARY
    )

    subtitle = header_data.get("subtitle", {})
    if subtitle.get("text"):
        add_text_box(
            slide,
            subtitle["text"],
            subtitle.get("x_mm", 15),
            subtitle.get("y_mm", 28),
            subtitle.get("width_mm", 390),
            subtitle.get("height_mm", 7),
            font_size_pt=subtitle.get("font_size_pt", 14),
            font_color=Colors.SECONDARY
        )


def render_section(slide, section_data: dict):
    """セクションを描画"""
    section_type = section_data.get("type", "text_block")

    # ヘッダー描画
    header = section_data.get("header", {})
    if header.get("text"):
        add_section_header(
            slide,
            header["text"],
            header["x_mm"],
            header["y_mm"],
            header["width_mm"]
        )

    # タイプ別描画
    if section_type == "bullets":
        render_bullets(slide, section_data)
    elif section_type == "table":
        render_table(slide, section_data)
    elif section_type == "flowchart":
        render_flowchart(slide, section_data)
    elif section_type == "kpi_box":
        render_kpi_box(slide, section_data)
    else:
        render_text_block(slide, section_data)


def render_bullets(slide, data: dict):
    """箇条書きを描画"""
    items = data.get("items", [])
    if not items:
        return

    first_item = items[0]
    x_mm = first_item.get("x_mm", 20)
    y_mm = first_item.get("y_mm", 50)
    width_mm = first_item.get("width_mm", 180)

    texts = [item.get("text", item) if isinstance(item, dict) else item
             for item in items]

    add_bullet_list(
        slide, texts,
        x_mm, y_mm, width_mm,
        height_mm=len(items) * 8 + 5
    )


def render_table(slide, data: dict):
    """表を描画"""
    table_data = data.get("table", {})
    add_table(
        slide,
        table_data.get("x_mm", 20),
        table_data.get("y_mm", 50),
        table_data.get("width_mm", 180),
        table_data.get("columns", []),
        table_data.get("rows", [])
    )


def render_flowchart(slide, data: dict):
    """フローチャートを描画"""
    steps = data.get("steps", [])
    if not steps:
        return

    header = data.get("header", {})
    add_flowchart(
        slide,
        steps,
        header.get("x_mm", 20),
        header.get("y_mm", 50) + 12,
        header.get("width_mm", 180),
        data.get("direction", "h")
    )


def render_kpi_box(slide, data: dict):
    """KPIボックスを描画"""
    value_data = data.get("value", {})

    # 背景ボックス
    add_box_with_background(
        slide,
        value_data.get("x_mm", 20) - 5,
        value_data.get("y_mm", 50) - 2,
        value_data.get("width_mm", 80) + 10,
        value_data.get("height_mm", 20) + 15
    )

    # 数値
    add_text_box(
        slide,
        value_data.get("text", ""),
        value_data.get("x_mm", 20),
        value_data.get("y_mm", 50),
        value_data.get("width_mm", 80),
        value_data.get("height_mm", 20),
        font_size_pt=value_data.get("font_size_pt", 32),
        font_bold=True,
        font_color=Colors.PRIMARY,
        alignment=PP_ALIGN.CENTER
    )

    # 単位・ラベル
    unit = data.get("unit", "")
    label = data.get("label", "")
    if unit or label:
        add_text_box(
            slide,
            f"{unit} {label}".strip(),
            value_data.get("x_mm", 20),
            value_data.get("y_mm", 50) + 22,
            value_data.get("width_mm", 80),
            10,
            font_size_pt=12,
            alignment=PP_ALIGN.CENTER
        )


def render_text_block(slide, data: dict):
    """テキストブロックを描画"""
    body = data.get("body", {})
    if body.get("text"):
        add_text_box_with_auto_shrink(
            slide,
            body["text"],
            body.get("x_mm", 20),
            body.get("y_mm", 50),
            body.get("width_mm", 180),
            body.get("height_mm", 50)
        )


def render_footer(slide, footer_data: dict):
    """フッターを描画"""
    if footer_data.get("text"):
        add_text_box(
            slide,
            footer_data["text"],
            footer_data.get("x_mm", 15),
            footer_data.get("y_mm", 275),
            footer_data.get("width_mm", 390),
            footer_data.get("height_mm", 12),
            font_size_pt=footer_data.get("font_size_pt", Fonts.FOOTER),
            font_color=Colors.SECONDARY
        )


# ヘルパー関数（前述の実装を使用）
def add_text_box(slide, text, x_mm, y_mm, width_mm, height_mm,
                 font_size_pt=14, font_bold=False,
                 font_color=Colors.SECONDARY,
                 alignment=PP_ALIGN.LEFT):
    shape = slide.shapes.add_textbox(
        Mm(x_mm), Mm(y_mm), Mm(width_mm), Mm(height_mm)
    )
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = Fonts.FAMILY
    p.font.size = Pt(font_size_pt)
    p.font.bold = font_bold
    p.font.color.rgb = font_color
    p.alignment = alignment
    return shape


def add_section_header(slide, text, x_mm, y_mm, width_mm):
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Mm(x_mm), Mm(y_mm), Mm(3), Mm(8)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = Colors.PRIMARY
    bar.line.fill.background()

    add_text_box(slide, text, x_mm + 5, y_mm, width_mm - 5, 10,
                 font_size_pt=Fonts.SECTION_HEADER, font_bold=True,
                 font_color=Colors.PRIMARY)


def add_bullet_list(slide, items, x_mm, y_mm, width_mm, height_mm):
    shape = slide.shapes.add_textbox(
        Mm(x_mm), Mm(y_mm), Mm(width_mm), Mm(height_mm)
    )
    tf = shape.text_frame
    tf.word_wrap = True

    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "・" + item
        p.font.name = Fonts.FAMILY
        p.font.size = Pt(Fonts.BODY)
        p.font.color.rgb = Colors.SECONDARY
        p.space_after = Pt(4)


def add_box_with_background(slide, x_mm, y_mm, width_mm, height_mm,
                            fill_color=Colors.ACCENT_BG,
                            border_color=Colors.BORDER):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Mm(x_mm), Mm(y_mm), Mm(width_mm), Mm(height_mm)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(0.5)
    return shape


def add_table(slide, x_mm, y_mm, width_mm, columns, rows):
    row_count = len(rows) + 1
    col_count = len(columns)

    table = slide.shapes.add_table(
        row_count, col_count,
        Mm(x_mm), Mm(y_mm),
        Mm(width_mm), Mm(row_count * 8)
    ).table

    col_width = Mm(width_mm / col_count)
    for col in table.columns:
        col.width = col_width

    for i, col_name in enumerate(columns):
        cell = table.cell(0, i)
        cell.text = col_name
        cell.fill.solid()
        cell.fill.fore_color.rgb = Colors.PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.font.name = Fonts.FAMILY
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = RgbColor(0xFF, 0xFF, 0xFF)
        p.alignment = PP_ALIGN.CENTER
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE

    for row_idx, row_data in enumerate(rows):
        for col_idx, cell_value in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = str(cell_value)
            if row_idx % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = Colors.ACCENT_BG
            p = cell.text_frame.paragraphs[0]
            p.font.name = Fonts.FAMILY
            p.font.size = Pt(11)
            p.font.color.rgb = Colors.SECONDARY
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE


def add_flowchart(slide, steps, x_mm, y_mm, width_mm, direction="h"):
    step_count = len(steps)

    if direction == "h":
        step_width = (width_mm - (step_count - 1) * 15) / step_count
        step_height = 25

        for i, step in enumerate(steps):
            step_x = x_mm + i * (step_width + 15)
            text = step.get("text", step) if isinstance(step, dict) else step

            add_box_with_background(slide, step_x, y_mm, step_width, step_height)
            add_text_box(slide, text, step_x + 2, y_mm + 5,
                        step_width - 4, step_height - 10,
                        font_size_pt=12, alignment=PP_ALIGN.CENTER)

            if i < step_count - 1:
                add_triangle_arrow(slide, step_x + step_width + 3,
                                  y_mm + step_height / 2 - 4, "right")


def add_triangle_arrow(slide, x_mm, y_mm, direction="right"):
    rotation = {"right": 90, "down": 180, "left": 270, "up": 0}[direction]

    shape = slide.shapes.add_shape(
        MSO_SHAPE.ISOSCELES_TRIANGLE,
        Mm(x_mm), Mm(y_mm), Mm(8), Mm(8)
    )
    shape.rotation = rotation
    shape.fill.solid()
    shape.fill.fore_color.rgb = Colors.PRIMARY
    shape.line.fill.background()


def add_text_box_with_auto_shrink(slide, text, x_mm, y_mm, width_mm, height_mm,
                                   initial_font_size_pt=14, min_font_size_pt=8,
                                   **kwargs):
    font_size = initial_font_size_pt
    while font_size >= min_font_size_pt:
        char_width = font_size * 0.35
        chars_per_line = int(width_mm / char_width)
        lines = (len(text) + chars_per_line - 1) // chars_per_line
        if lines * font_size * 0.42 <= height_mm:
            break
        font_size -= 1

    return add_text_box(slide, text, x_mm, y_mm, width_mm, height_mm,
                        font_size_pt=font_size, **kwargs)
```
