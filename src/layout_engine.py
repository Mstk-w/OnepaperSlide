"""
OnePaperSlide レイアウトエンジン
JSON構造化データを座標付きレイアウトデータに変換
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

from logging_config import get_logger

# モジュールロガー
logger = get_logger("layout_engine")

# 設定ファイルから読み込むためのインポート
from config import config
from custom_types import AIOutput, SlideLayoutData, HeaderLayout, FooterLayout


def _get_layout_values():
    """設定ファイルからレイアウト値を取得するヘルパー関数"""
    cfg = config
    return {
        "slide_width": cfg.slide.width_mm,
        "slide_height": cfg.slide.height_mm,
        "margin_top": cfg.margins.top_mm,
        "margin_bottom": cfg.margins.bottom_mm,
        "margin_left": cfg.margins.left_mm,
        "margin_right": cfg.margins.right_mm,
        "header_height": cfg.header_height_mm,
        "footer_height": cfg.footer_height_mm,
        "column_gap": cfg.grid.column_gap_mm,
        "column_count": cfg.grid.column_count,
        "section_gap": cfg.grid.section_gap_mm,
    }


class LayoutConstants:
    """
    レイアウト定数（A3横: 420mm × 297mm）
    設定ファイル(settings.yaml)から値を読み込み、後方互換性を維持
    """
    # 設定ファイルから値を読み込み
    _cfg = _get_layout_values()
    
    SLIDE_WIDTH = _cfg["slide_width"]
    SLIDE_HEIGHT = _cfg["slide_height"]
    MARGIN_TOP = _cfg["margin_top"]
    MARGIN_BOTTOM = _cfg["margin_bottom"]
    MARGIN_LEFT = _cfg["margin_left"]
    MARGIN_RIGHT = _cfg["margin_right"]
    HEADER_HEIGHT = _cfg["header_height"]
    FOOTER_HEIGHT = _cfg["footer_height"]
    COLUMN_GAP = _cfg["column_gap"]
    COLUMN_COUNT = _cfg["column_count"]
    SECTION_GAP = _cfg["section_gap"]

    @classmethod
    def content_width(cls) -> float:
        """コンテンツ領域の幅"""
        return cls.SLIDE_WIDTH - cls.MARGIN_LEFT - cls.MARGIN_RIGHT

    @classmethod
    def content_height(cls) -> float:
        """コンテンツ領域の高さ（本文エリア）"""
        return (cls.SLIDE_HEIGHT - cls.MARGIN_TOP - cls.MARGIN_BOTTOM
                - cls.HEADER_HEIGHT - cls.FOOTER_HEIGHT)

    @classmethod
    def column_width(cls) -> float:
        """1カラムの幅"""
        total_gap = cls.COLUMN_GAP * (cls.COLUMN_COUNT - 1)
        return (cls.content_width() - total_gap) / cls.COLUMN_COUNT


@dataclass
class SectionPlacement:
    """セクションの配置情報"""
    section_id: str
    column: int
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float


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


def estimate_section_height(section: dict) -> float:
    """セクションの高さを推定"""
    section_type = section.get("type", "text_block")
    header_height = 10  # mm

    content = section.get("content", {})

    if section_type == "bullets":
        items = content.get("items", [])
        return header_height + len(items) * 8 + 5

    elif section_type == "table":
        rows = content.get("rows", [])
        return header_height + (len(rows) + 1) * 8 + 5

    elif section_type == "flowchart":
        steps = content.get("steps", [])
        direction = content.get("direction", "h")
        if direction == "h":
            return header_height + 40
        else:
            return header_height + len(steps) * 25 + 5

    elif section_type == "kpi_box":
        return header_height + 35

    else:  # text_block
        text = content.get("text", "") if isinstance(content, dict) else str(content)
        lines = max(1, len(text) // 40 + 1)
        return header_height + lines * 6 + 5


def _distribute_sections_default(sections: List[dict]) -> List[SectionPlacement]:
    """デフォルトの配置ロジック（単純積み上げ）"""
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
        # カラムインデックスの境界チェック
        if col_idx < 0 or col_idx >= len(grid["columns"]):
            logger.warning(f"Invalid column index {col_idx} for section {section.get('id')}. defaulting to 0.")
            col_idx = 0

        estimated_height = estimate_section_height(section)

        placement = SectionPlacement(
            section_id=section.get("id", "unknown"),
            column=col_idx,
            x_mm=grid["columns"][col_idx]["x"],
            y_mm=column_y[col_idx],
            width_mm=lc.column_width(),
            height_mm=estimated_height
        )
        placements.append(placement)
        column_y[col_idx] += estimated_height + lc.SECTION_GAP

    return placements


def _distribute_sections_with_template(
    sections: List[dict], 
    template: dict
) -> List[SectionPlacement]:
    """テンプレート定義に基づく配置ロジック"""
    lc = LayoutConstants
    grid = calculate_grid()
    placements: List[SectionPlacement] = []
    
    # テンプレートのセクション定義を取得
    template_sections = template.get("body", {}).get("sections", [])
    if not template_sections:
        return _distribute_sections_default(sections)

    # 現在のY座標（カラムごと）
    column_y = [
        grid["columns"][0]["y"],
        grid["columns"][1]["y"]
    ]

    # AI出力セクションとテンプレート定義のマッチング
    # 戦略: 順序ベースでマッチング（IDマッチングはAIが正確なIDを返さない可能性があるため補助的に使用）
    
    # マッチング済みのAI出力インデックス
    used_indices = set()
    
    for tmpl_sec in template_sections:
        # このテンプレート定義に対応するAI出力を探す
        target_section = None
        
        # 1. IDで完全一致を探す
        for i, sec in enumerate(sections):
            if i in used_indices:
                continue
            if sec.get("id") == tmpl_sec.get("id"):
                target_section = sec
                used_indices.add(i)
                break
        
        # 2. 見つからない場合、順序（order）で探す
        # テンプレートのorderは1始まりと仮定
        if not target_section:
            order = tmpl_sec.get("order", 0)
            column = tmpl_sec.get("column", 0)
            
            # 同じカラムで、まだ使われていないセクションを割り当てる
            # ここは簡易的に、AI出力のリスト順に割り当てていく（カラムは無視される可能性があるが、テンプレート優先）
            for i, sec in enumerate(sections):
                if i in used_indices:
                    continue
                # AI出力のカラム指定があればそれを尊重、なければテンプレートのカラム
                sec_col = sec.get("column", column)
                
                # 境界チェック（テンプレートのカラムは信頼するが、AI指定の場合はチェックが必要）
                if sec_col < 0 or sec_col >= len(grid["columns"]):
                    sec_col = 0
                
                if sec_col == column:
                    target_section = sec
                    used_indices.add(i)
                    break

        if target_section:
            # 配置計算
            col_idx = tmpl_sec.get("column", 0)
            min_h = tmpl_sec.get("min_height_mm", 0)
            max_h = tmpl_sec.get("max_height_mm", 999)
            
            # コンテンツ量から高さを推定
            estimated = estimate_section_height(target_section)
            
            # 制約適用
            height = max(min_h, min(estimated, max_h))
            
            placement = SectionPlacement(
                section_id=target_section.get("id", tmpl_sec.get("id")),
                column=col_idx,
                x_mm=grid["columns"][col_idx]["x"],
                y_mm=column_y[col_idx],
                width_mm=lc.column_width(),
                height_mm=height
            )
            placements.append(placement)
            column_y[col_idx] += height + lc.SECTION_GAP

    # テンプレート定義にマッチしなかった残りのAI出力セクション
    # これらは無視するか、空いている場所に配置するか？
    # 今回は単純に末尾に追加（デフォルト配置ロジックに近い形）
    for i, sec in enumerate(sections):
        if i not in used_indices:
            col_idx = sec.get("column", 0)
            # カラムインデックスの境界チェック
            if col_idx < 0 or col_idx >= len(grid["columns"]):
                logger.warning(f"Invalid column index {col_idx} for extra section {sec.get('id')}. defaulting to 0.")
                col_idx = 0
            estimated = estimate_section_height(sec)
            placement = SectionPlacement(
                section_id=sec.get("id", f"extra_{i}"),
                column=col_idx,
                x_mm=grid["columns"][col_idx]["x"],
                y_mm=column_y[col_idx],
                width_mm=lc.column_width(),
                height_mm=estimated
            )
            placements.append(placement)
            column_y[col_idx] += estimated + lc.SECTION_GAP

    return placements


def distribute_sections(
    sections: List[dict],
    template: Optional[dict] = None
) -> List[SectionPlacement]:
    """セクションをカラムに分配（テンプレート対応）"""
    if template:
        return _distribute_sections_with_template(sections, template)
    return _distribute_sections_default(sections)


def load_component_config(component_id: str) -> dict:
    """コンポーネント設定JSONを読み込み"""
    config_path = Path(__file__).parent.parent / "components" / f"{component_id}.json"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("default_style", {})
        except Exception as e:
            logger.error(f"Failed to load component config {component_id}: {e}")
    return {}


def layout_bullets(section: dict, placement: SectionPlacement) -> dict:
    """箇条書きコンポーネントのレイアウト"""
    # 設定読み込み
    style = load_component_config("bullets")
    
    bullet_char = style.get("bullet_char", "・")
    indent_mm = style.get("indent_mm", 5)
    line_spacing_mm = style.get("line_spacing_mm", 8)
    # font_size_pt = style.get("font_size_pt", 14) # 現在はpptx_builder側で制御しているため、ここでは使用しないが、将来的には渡すべき
    
    content = section.get("content", {})
    items = content.get("items", [])

    bullet_layouts = []
    y_offset = 10

    for i, item in enumerate(items):
        text = item if isinstance(item, str) else item.get("text", "")
        # バレット文字を付加（pptx側で処理しない場合）
        display_text = f"{bullet_char}{text}" if not text.startswith(bullet_char) else text
        
        bullet_layouts.append({
            "text": display_text,
            "x_mm": placement.x_mm + indent_mm,
            "y_mm": placement.y_mm + y_offset + i * line_spacing_mm,
            "width_mm": placement.width_mm - (indent_mm * 2),
            "height_mm": line_spacing_mm - 1,
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


def layout_table(section: dict, placement: SectionPlacement) -> dict:
    """表コンポーネントのレイアウト"""
    # 設定読み込み
    style = load_component_config("table")
    header_height_mm = style.get("header_height_mm", 8)
    row_height_mm = style.get("row_height_mm", 8)
    
    content = section.get("content", {})
    columns = content.get("columns", [])
    rows = content.get("rows", [])

    col_count = len(columns) if columns else 1
    row_count = len(rows) + 1

    table_width = placement.width_mm - 4
    table_height = row_count * row_height_mm
    col_width = table_width / col_count
    
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
            "row_height_mm": row_height_mm
        }
    }


def layout_flowchart(section: dict, placement: SectionPlacement) -> dict:
    """フローチャートコンポーネントのレイアウト"""
    # 設定読み込み
    style = load_component_config("flowchart")
    step_height_h = style.get("step_height_mm", 25) # 水平時の高さ
    step_height_v = 18 # 垂直時の高さ（JSON未定義ならハードコード維持）
    
    content = section.get("content", {})
    steps = content.get("steps", [])
    direction = content.get("direction", "h")

    step_layouts = []
    step_count = len(steps) if steps else 0

    if step_count == 0:
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
            "steps": []
        }

    if direction == "h":
        step_width = (placement.width_mm - 10) / step_count - 5
        step_height = step_height_h

        for i, step in enumerate(steps):
            text = step if isinstance(step, str) else step.get("text", "")
            x = placement.x_mm + 5 + i * (step_width + 5)
            step_layouts.append({
                "text": text,
                "x_mm": x,
                "y_mm": placement.y_mm + 12,
                "width_mm": step_width,
                "height_mm": step_height,
                "show_arrow": i < step_count - 1
            })
    else:
        step_width = placement.width_mm - 20
        step_height = step_height_v

        for i, step in enumerate(steps):
            text = step if isinstance(step, str) else step.get("text", "")
            y = placement.y_mm + 12 + i * (step_height + 7)
            step_layouts.append({
                "text": text,
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


def layout_kpi_box(section: dict, placement: SectionPlacement) -> dict:
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


def layout_text_block(section: dict, placement: SectionPlacement) -> dict:
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


def load_template(template_id: str) -> Optional[dict]:
    """テンプレートJSONを読み込み"""
    template_map = {
        "T1": "T1_problem_solving",
        "T2": "T2_comparison",
        "T3": "T3_policy_proposal",
        "T4": "T4_workflow"
    }

    filename = template_map.get(template_id, template_id)
    template_path = Path(__file__).parent.parent / "templates" / f"{filename}.json"

    if template_path.exists():
        try:
            with open(template_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load template {filename}: {e}")
            return None
    return None





def process_layout(ai_output: AIOutput) -> SlideLayoutData:
    """
    AI出力を座標付きレイアウトデータに変換

    Args:
        ai_output: AI生成の構造化データ

    Returns:
        座標情報を含むレイアウトデータ
    """
    lc = LayoutConstants
    template_id = ai_output.get("recommended_template", "T1")

    # テンプレート読み込み
    template = load_template(template_id)
    if not template:
        logger.warning(f"Template {template_id} not found, using default layout logic")
    
    # ヘッダーレイアウト
    header_layout: HeaderLayout = {
        "title": {
            "text": ai_output.get("title", "無題"),
            "x_mm": lc.MARGIN_LEFT,
            "y_mm": lc.MARGIN_TOP,
            "width_mm": lc.content_width(),
            "height_mm": 15,
            "font_size_pt": config.typography.title_size,
            "font_bold": True,
            "font_color": None,
            "alignment": "LEFT"
        },
        "subtitle": {
            "text": ai_output.get("subtitle", ""),
            "x_mm": lc.MARGIN_LEFT,
            "y_mm": lc.MARGIN_TOP + 18,
            "width_mm": lc.content_width(),
            "height_mm": 7,
            "font_size_pt": config.typography.body_size,  # subtitleサイズがないのでbodyで代用
            "font_bold": False,
            "font_color": None,
            "alignment": "LEFT"
        }
    }

    # セクション配置
    sections = ai_output.get("sections", [])
    # テンプレートがある場合はそれを渡し、なければNone（デフォルトロジック）
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
    footer_layout: FooterLayout = {
        "text": ai_output.get("footer_note", ""),
        "x_mm": lc.MARGIN_LEFT,
        "y_mm": lc.SLIDE_HEIGHT - lc.MARGIN_BOTTOM - lc.FOOTER_HEIGHT,
        "width_mm": lc.content_width(),
        "height_mm": lc.FOOTER_HEIGHT,
        "font_size_pt": config.typography.footer_size
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
