"""
Layout Engine Unit Tests
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from layout_engine import (
    LayoutConstants,
    calculate_grid,
    distribute_sections,
    estimate_section_height,
    process_layout
)


class TestLayoutConstants:
    """レイアウト定数のテスト"""

    def test_slide_dimensions(self):
        """A3横サイズの確認"""
        assert LayoutConstants.SLIDE_WIDTH == 420
        assert LayoutConstants.SLIDE_HEIGHT == 297

    def test_content_width(self):
        """コンテンツ幅の計算"""
        expected = 420 - 15 - 15  # SLIDE_WIDTH - 左右余白
        assert LayoutConstants.content_width() == expected

    def test_column_width(self):
        """カラム幅の計算"""
        content_width = LayoutConstants.content_width()
        column_gap = LayoutConstants.COLUMN_GAP
        expected = (content_width - column_gap) / 2
        assert LayoutConstants.column_width() == expected


class TestCalculateGrid:
    """グリッド計算のテスト"""

    def test_grid_has_required_keys(self):
        """グリッドに必要なキーが存在"""
        grid = calculate_grid()
        assert "header" in grid
        assert "body" in grid
        assert "footer" in grid
        assert "columns" in grid

    def test_columns_count(self):
        """カラム数が2"""
        grid = calculate_grid()
        assert len(grid["columns"]) == 2

    def test_columns_no_overlap(self):
        """カラムが重ならない"""
        grid = calculate_grid()
        col1 = grid["columns"][0]
        col2 = grid["columns"][1]

        col1_right = col1["x"] + col1["width"]
        assert col1_right <= col2["x"]


class TestEstimateSectionHeight:
    """セクション高さ推定のテスト"""

    def test_bullets_height(self):
        """箇条書きの高さ推定"""
        section = {
            "type": "bullets",
            "content": {"items": ["item1", "item2", "item3"]}
        }
        height = estimate_section_height(section)
        assert height > 0
        assert height >= 10 + 3 * 8  # ヘッダー + 3項目

    def test_table_height(self):
        """表の高さ推定"""
        section = {
            "type": "table",
            "content": {
                "columns": ["A", "B"],
                "rows": [["1", "2"], ["3", "4"]]
            }
        }
        height = estimate_section_height(section)
        assert height > 0

    def test_flowchart_height_horizontal(self):
        """横フローチャートの高さ"""
        section = {
            "type": "flowchart",
            "content": {"steps": ["1", "2", "3"], "direction": "h"}
        }
        height = estimate_section_height(section)
        assert height >= 50  # ヘッダー + 固定高さ


class TestProcessLayout:
    """レイアウト処理のテスト"""

    def test_returns_dict(self, sample_ai_output):
        """辞書を返す"""
        result = process_layout(sample_ai_output)
        assert isinstance(result, dict)

    def test_has_required_keys(self, sample_ai_output):
        """必須キーが存在"""
        result = process_layout(sample_ai_output)
        assert "template_id" in result
        assert "slide" in result
        assert "header" in result
        assert "sections" in result
        assert "footer" in result

    def test_slide_dimensions(self, sample_ai_output):
        """スライドサイズが正しい"""
        result = process_layout(sample_ai_output)
        assert result["slide"]["width_mm"] == 420
        assert result["slide"]["height_mm"] == 297

    def test_sections_have_coordinates(self, sample_ai_output):
        """セクションに座標がある"""
        result = process_layout(sample_ai_output)
        for section in result["sections"]:
            assert "header" in section
            header = section["header"]
            assert "x_mm" in header
            assert "y_mm" in header
            assert "width_mm" in header
