"""
OnePaperSlide 設定管理モジュール
settings.yamlから設定を読み込み、アプリケーション全体で使用
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from logging_config import get_logger

logger = get_logger("config")

# 設定ファイルのパス
SETTINGS_PATH = Path(__file__).parent.parent / "settings.yaml"


@dataclass
class SlideSettings:
    """スライドサイズ設定"""
    width_mm: int
    height_mm: int
    background_color: str


@dataclass
class MarginSettings:
    """余白設定"""
    top_mm: int
    bottom_mm: int
    left_mm: int
    right_mm: int


@dataclass
class GridSettings:
    """グリッド設定"""
    column_count: int
    column_gap_mm: int
    section_gap_mm: int


@dataclass
class ColorSettings:
    """カラーパレット設定"""
    primary: str
    secondary: str
    background: str
    accent_bg: str
    border: str
    alert: str


@dataclass
class TypographySettings:
    """タイポグラフィ設定"""
    font_family: str
    title_size: int
    section_header_size: int
    body_size: int
    footer_size: int
    table_header_size: int
    table_body_size: int


@dataclass
class AutoShrinkSettings:
    """自動縮小設定"""
    min_font_size_pt: int
    shrink_step_pt: int


@dataclass
class AISettings:
    """AI設定"""
    default_model: str
    temperature: float
    top_p: float
    max_output_tokens: int
    max_retries: int


@dataclass
class AppSettings:
    """アプリケーション設定"""
    max_input_chars: int
    rate_limit_requests_per_minute: int


class Config:
    """
    アプリケーション設定を管理するシングルトンクラス
    settings.yamlから設定を読み込み、各種設定オブジェクトを提供
    """
    _instance: Optional["Config"] = None
    _raw_config: Dict[str, Any] = {}
    _overrides: Dict[str, Any] = {}
    
    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
            cls._instance._overrides = {}
        return cls._instance
    
    def _load_config(self) -> None:
        """設定ファイルを読み込み"""
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, encoding="utf-8") as f:
                self._raw_config = yaml.safe_load(f) or {}
            logger.info(f"設定ファイルを読み込みました: {SETTINGS_PATH}")
        else:
            logger.warning(f"設定ファイルが見つかりません: {SETTINGS_PATH}、デフォルト値を使用")
            self._raw_config = {}

    def override_colors(self, primary: Optional[str] = None, background: Optional[str] = None) -> None:
        """カラー設定を一時的に上書き"""
        if "colors" not in self._overrides:
            self._overrides["colors"] = {}
            
        if primary:
            self._overrides["colors"]["primary"] = primary
        if background:
            self._overrides["colors"]["background"] = background
            
    def reset_overrides(self) -> None:
        """オーバーライドをリセット"""
        self._overrides = {}
    
    def reload(self) -> None:
        """設定を再読み込み"""
        self._load_config()
    
    @property
    def slide(self) -> SlideSettings:
        """スライド設定を取得"""
        slide_config = self._raw_config.get("slide", {})
        return SlideSettings(
            width_mm=slide_config.get("width_mm", 420),
            height_mm=slide_config.get("height_mm", 297),
            background_color=slide_config.get("background_color", "#FFFFFF")
        )
    
    @property
    def margins(self) -> MarginSettings:
        """余白設定を取得"""
        margin_config = self._raw_config.get("margins", {})
        return MarginSettings(
            top_mm=margin_config.get("top_mm", 10),
            bottom_mm=margin_config.get("bottom_mm", 10),
            left_mm=margin_config.get("left_mm", 15),
            right_mm=margin_config.get("right_mm", 15)
        )
    
    @property
    def grid(self) -> GridSettings:
        """グリッド設定を取得"""
        grid_config = self._raw_config.get("grid", {})
        return GridSettings(
            column_count=grid_config.get("column_count", 2),
            column_gap_mm=grid_config.get("column_gap_mm", 10),
            section_gap_mm=grid_config.get("section_gap_mm", 8)
        )
    
    @property
    def header_height_mm(self) -> int:
        """ヘッダー高さを取得"""
        return self._raw_config.get("header", {}).get("height_mm", 25)
    
    @property
    def footer_height_mm(self) -> int:
        """フッター高さを取得"""
        return self._raw_config.get("footer", {}).get("height_mm", 12)
    
    @property
    def colors(self) -> ColorSettings:
        """カラー設定を取得（オーバーライド考慮）"""
        colors_config = self._raw_config.get("colors", {})
        overrides = self._overrides.get("colors", {})
        
        return ColorSettings(
            primary=overrides.get("primary", colors_config.get("primary", "#2B6CB0")),
            secondary=colors_config.get("secondary", "#4A5568"),
            background=overrides.get("background", colors_config.get("background", "#FFFFFF")),
            accent_bg=colors_config.get("accent_bg", "#EBF8FF"),
            border=colors_config.get("border", "#E2E8F0"),
            alert=colors_config.get("alert", "#C53030")
        )
    
    @property
    def typography(self) -> TypographySettings:
        """タイポグラフィ設定を取得"""
        typography_config = self._raw_config.get("typography", {})
        sizes = typography_config.get("sizes", {})
        return TypographySettings(
            font_family=typography_config.get("font_family", "メイリオ"),
            title_size=sizes.get("title", 28),
            section_header_size=sizes.get("section_header", 18),
            body_size=sizes.get("body", 14),
            footer_size=sizes.get("footer", 10),
            table_header_size=sizes.get("table_header", 12),
            table_body_size=sizes.get("table_body", 11)
        )
    
    @property
    def auto_shrink(self) -> AutoShrinkSettings:
        """自動縮小設定を取得"""
        shrink_config = self._raw_config.get("auto_shrink", {})
        return AutoShrinkSettings(
            min_font_size_pt=shrink_config.get("min_font_size_pt", 8),
            shrink_step_pt=shrink_config.get("shrink_step_pt", 1)
        )
    
    @property
    def ai(self) -> AISettings:
        """AI設定を取得"""
        ai_config = self._raw_config.get("ai", {})
        return AISettings(
            default_model=ai_config.get("default_model", "gemini-2.0-flash"),
            temperature=ai_config.get("temperature", 0.3),
            top_p=ai_config.get("top_p", 0.95),
            max_output_tokens=ai_config.get("max_output_tokens", 8192),
            max_retries=ai_config.get("max_retries", 3)
        )
    
    @property
    def app(self) -> AppSettings:
        """アプリケーション設定を取得"""
        app_config = self._raw_config.get("app", {})
        rate_limit = app_config.get("rate_limit", {})
        return AppSettings(
            max_input_chars=app_config.get("max_input_chars", 10000),
            rate_limit_requests_per_minute=rate_limit.get("requests_per_minute", 5)
        )


# グローバルインスタンス
config = Config()
