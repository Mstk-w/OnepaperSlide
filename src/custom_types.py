"""
OnePaperSlide 型定義モジュール
アプリケーション全体で使用する共有型定義
"""

from typing import TypedDict, List, Optional, Union, Literal, Dict, Any

# ==========================================
# AI出力構造 (input to LayoutEngine)
# ==========================================

class SectionContent(TypedDict, total=False):
    """セクションコンテンツの内訳（各タイプの和集合）"""
    # bullets
    items: List[str]
    
    # table
    columns: List[str]
    rows: List[List[str]]
    
    # flowchart
    steps: List[str]
    direction: Literal["h", "v"]
    
    # kpi_box
    value: str
    unit: str
    label: str
    
    # text_block
    text: str

class AISection(TypedDict):
    """AIが生成するセクション情報"""
    id: str
    column: int
    header: str
    type: Literal["bullets", "table", "flowchart", "kpi_box", "text_block"]
    content: SectionContent

class AIOutput(TypedDict):
    """AI生成データの全体構造"""
    recommended_template: Literal["T1", "T2", "T3", "T4"]
    title: str
    subtitle: Optional[str]
    sections: List[AISection]
    footer_note: Optional[str]

# ==========================================
# レイアウト構造 (output of LayoutEngine)
# ==========================================

class ElementLayout(TypedDict):
    """基本要素のレイアウト情報"""
    text: str
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    font_size_pt: int
    font_bold: Optional[bool]
    font_color: Optional[Any] # RGBColorオブジェクトなど
    alignment: Optional[str] # "LEFT", "CENTER", "RIGHT"

class HeaderLayout(TypedDict):
    """ヘッダー領域のレイアウト"""
    title: ElementLayout
    subtitle: ElementLayout

class FooterLayout(TypedDict):
    """フッター領域のレイアウト"""
    text: str
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    font_size_pt: int

class SlideSize(TypedDict):
    """スライドサイズ"""
    width_mm: int
    height_mm: int

class SlideLayoutData(TypedDict):
    """PPTX生成に必要な全レイアウト情報"""
    template_id: str
    slide: SlideSize
    header: HeaderLayout
    sections: List[Dict[str, Any]] # 各セクションの具体的なレイアウト（構造が可変なためDict）
    footer: FooterLayout
