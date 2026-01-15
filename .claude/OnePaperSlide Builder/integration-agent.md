# Integration-Agent: 統合テスト・検証ガイド

## 担当ファイル

- `tests/test_layout_engine.py`
- `tests/test_pptx_builder.py`
- `tests/test_ai_service.py`
- `tests/conftest.py`

## 目次

1. [テスト環境セットアップ](#1-テスト環境セットアップ)
2. [ユニットテスト](#2-ユニットテスト)
3. [統合テスト](#3-統合テスト)
4. [E2Eテスト](#4-e2eテスト)
5. [パフォーマンス計測](#5-パフォーマンス計測)
6. [品質チェックリスト](#6-品質チェックリスト)

---

## 1. テスト環境セットアップ

### pytest設定

**requirements-dev.txt**
```
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-asyncio>=0.21.0
```

**pytest.ini**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
```

### conftest.py

```python
"""
pytest fixtures for OnePaperSlide tests
"""

import pytest
import json
from pathlib import Path
import sys

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_memo_text():
    """サンプル入力テキスト"""
    return """
現状:
- 紙ベースの申請処理で時間がかかっている
- 1件あたり平均30分の処理時間

課題:
- 手作業による転記ミスが頻発
- 承認フローが非効率

解決策:
- オンライン申請システムの導入
- 自動入力チェック機能

期待効果:
- 処理時間50%削減
- ミス率80%減少
"""


@pytest.fixture
def sample_ai_output():
    """サンプルAI出力"""
    return {
        "recommended_template": "T1",
        "title": "申請処理システム改善提案",
        "subtitle": "業務効率化に向けた取り組み",
        "sections": [
            {
                "id": "section_1",
                "column": 0,
                "header": "現状",
                "type": "bullets",
                "content": {
                    "items": [
                        "紙ベースの申請処理",
                        "1件あたり平均30分"
                    ]
                }
            },
            {
                "id": "section_2",
                "column": 0,
                "header": "課題",
                "type": "bullets",
                "content": {
                    "items": [
                        "転記ミスが頻発",
                        "承認フローが非効率"
                    ]
                }
            },
            {
                "id": "section_3",
                "column": 1,
                "header": "解決策",
                "type": "bullets",
                "content": {
                    "items": [
                        "オンライン申請システム導入",
                        "自動入力チェック機能"
                    ]
                }
            },
            {
                "id": "section_4",
                "column": 1,
                "header": "期待効果",
                "type": "kpi_box",
                "content": {
                    "value": "50",
                    "unit": "%",
                    "label": "処理時間削減"
                }
            }
        ],
        "footer_note": "情報システム課 担当: 山田"
    }


@pytest.fixture
def sample_layout_data(sample_ai_output):
    """サンプルレイアウトデータ"""
    from layout_engine import process_layout
    return process_layout(sample_ai_output)


@pytest.fixture
def template_t1():
    """T1テンプレートJSON"""
    template_path = Path(__file__).parent.parent / "templates" / "T1_problem_solving.json"
    if template_path.exists():
        with open(template_path, encoding="utf-8") as f:
            return json.load(f)
    return None
```

---

## 2. ユニットテスト

### test_layout_engine.py

```python
"""
Layout Engine Unit Tests
"""

import pytest
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
```

### test_pptx_builder.py

```python
"""
PPTX Builder Unit Tests
"""

import pytest
from io import BytesIO
from pptx import Presentation
from pptx.util import Mm

from pptx_builder import (
    build_pptx,
    add_text_box,
    add_section_header,
    add_table,
    Colors,
    Fonts
)


class TestBuildPptx:
    """PPTX生成のテスト"""

    def test_returns_bytes(self, sample_layout_data):
        """バイト列を返す"""
        result = build_pptx(sample_layout_data)
        assert isinstance(result, bytes)

    def test_valid_pptx(self, sample_layout_data):
        """有効なPPTXファイル"""
        result = build_pptx(sample_layout_data)
        prs = Presentation(BytesIO(result))
        assert len(prs.slides) == 1

    def test_slide_size(self, sample_layout_data):
        """スライドサイズが正しい"""
        result = build_pptx(sample_layout_data)
        prs = Presentation(BytesIO(result))
        assert prs.slide_width == Mm(420)
        assert prs.slide_height == Mm(297)

    def test_has_shapes(self, sample_layout_data):
        """図形が配置されている"""
        result = build_pptx(sample_layout_data)
        prs = Presentation(BytesIO(result))
        slide = prs.slides[0]
        assert len(slide.shapes) > 0


class TestAddTextBox:
    """テキストボックス追加のテスト"""

    @pytest.fixture
    def blank_slide(self):
        """空白スライド"""
        prs = Presentation()
        prs.slide_width = Mm(420)
        prs.slide_height = Mm(297)
        return prs.slides.add_slide(prs.slide_layouts[6])

    def test_adds_shape(self, blank_slide):
        """図形が追加される"""
        initial_count = len(blank_slide.shapes)
        add_text_box(blank_slide, "Test", 10, 10, 100, 20)
        assert len(blank_slide.shapes) == initial_count + 1

    def test_text_content(self, blank_slide):
        """テキストが正しい"""
        shape = add_text_box(blank_slide, "Hello", 10, 10, 100, 20)
        assert shape.text_frame.paragraphs[0].text == "Hello"


class TestColors:
    """カラー定義のテスト"""

    def test_primary_color(self):
        """プライマリカラーの確認"""
        assert Colors.PRIMARY is not None

    def test_from_hex(self):
        """16進数変換"""
        color = Colors.from_hex("#2B6CB0")
        assert color is not None
```

### test_ai_service.py

```python
"""
AI Service Unit Tests
"""

import pytest
from unittest.mock import Mock, patch

from ai_service import (
    parse_response,
    validate_output,
    fix_output,
    build_prompt,
    AIServiceError
)


class TestParseResponse:
    """JSON解析のテスト"""

    def test_parse_valid_json(self):
        """有効なJSONをパース"""
        json_str = '{"title": "Test", "sections": []}'
        result = parse_response(json_str)
        assert result["title"] == "Test"

    def test_parse_json_in_code_block(self):
        """コードブロック内のJSONをパース"""
        response = '''
        Here is the result:
        ```json
        {"title": "Test", "sections": []}
        ```
        '''
        result = parse_response(response)
        assert result["title"] == "Test"

    def test_parse_invalid_json_raises(self):
        """無効なJSONでエラー"""
        with pytest.raises(AIServiceError):
            parse_response("not json at all")


class TestValidateOutput:
    """出力バリデーションのテスト"""

    def test_valid_output(self, sample_ai_output):
        """有効な出力"""
        is_valid, error = validate_output(sample_ai_output)
        assert is_valid is True
        assert error is None

    def test_missing_title(self):
        """タイトル欠落"""
        data = {"recommended_template": "T1", "sections": []}
        is_valid, error = validate_output(data)
        assert is_valid is False
        assert "title" in error

    def test_invalid_template(self):
        """無効なテンプレート"""
        data = {
            "recommended_template": "T99",
            "title": "Test",
            "sections": []
        }
        is_valid, error = validate_output(data)
        assert is_valid is False


class TestFixOutput:
    """出力修正のテスト"""

    def test_normalize_template_id(self):
        """テンプレートID正規化"""
        data = {"recommended_template": "t1", "sections": []}
        result = fix_output(data)
        assert result["recommended_template"] == "T1"

    def test_add_missing_section_id(self):
        """セクションID自動付与"""
        data = {
            "recommended_template": "T1",
            "sections": [{"type": "bullets"}]
        }
        result = fix_output(data)
        assert result["sections"][0]["id"] == "section_1"

    def test_add_default_column(self):
        """デフォルトカラム付与"""
        data = {
            "recommended_template": "T1",
            "sections": [{"id": "s1", "type": "bullets"}]
        }
        result = fix_output(data)
        assert "column" in result["sections"][0]


class TestBuildPrompt:
    """プロンプト構築のテスト"""

    def test_includes_memo(self):
        """メモが含まれる"""
        prompt = build_prompt("Test memo")
        assert "Test memo" in prompt

    def test_includes_template_id(self):
        """テンプレートIDが含まれる"""
        prompt = build_prompt("Test", template_id="T2")
        assert "T2" in prompt
```

---

## 3. 統合テスト

### test_integration.py

```python
"""
Integration Tests
"""

import pytest
from pathlib import Path


class TestFullPipeline:
    """フルパイプラインのテスト"""

    @pytest.mark.integration
    def test_memo_to_pptx(self, sample_memo_text):
        """メモからPPTXまでの全体フロー"""
        # このテストはAPIキーが必要
        # CI環境ではスキップ
        pytest.skip("Requires API key")

    def test_ai_output_to_pptx(self, sample_ai_output):
        """AI出力からPPTXまで"""
        from layout_engine import process_layout
        from pptx_builder import build_pptx

        layout_data = process_layout(sample_ai_output)
        pptx_bytes = build_pptx(layout_data)

        assert len(pptx_bytes) > 0

    def test_all_templates(self, sample_ai_output):
        """全テンプレートで生成"""
        from layout_engine import process_layout
        from pptx_builder import build_pptx

        for template_id in ["T1", "T2", "T3", "T4"]:
            sample_ai_output["recommended_template"] = template_id
            layout_data = process_layout(sample_ai_output)
            pptx_bytes = build_pptx(layout_data)
            assert len(pptx_bytes) > 0


class TestLayoutPrecision:
    """レイアウト精度のテスト"""

    def test_no_section_overlap(self, sample_layout_data):
        """セクションが重ならない"""
        sections = sample_layout_data["sections"]

        for i, s1 in enumerate(sections):
            for s2 in sections[i+1:]:
                h1 = s1["header"]
                h2 = s2["header"]

                # 同じカラムの場合のみチェック
                if h1.get("x_mm") == h2.get("x_mm"):
                    # Y座標の重なりチェック
                    s1_bottom = h1["y_mm"] + h1["height_mm"]
                    s2_top = h2["y_mm"]
                    assert s1_bottom <= s2_top or h2["y_mm"] + h2["height_mm"] <= h1["y_mm"]

    def test_sections_within_bounds(self, sample_layout_data):
        """セクションがスライド範囲内"""
        slide_width = sample_layout_data["slide"]["width_mm"]
        slide_height = sample_layout_data["slide"]["height_mm"]

        for section in sample_layout_data["sections"]:
            header = section["header"]
            assert header["x_mm"] >= 0
            assert header["y_mm"] >= 0
            assert header["x_mm"] + header["width_mm"] <= slide_width
            assert header["y_mm"] + header["height_mm"] <= slide_height
```

---

## 4. E2Eテスト

### test_e2e.py

```python
"""
End-to-End Tests (Manual)
"""

import pytest
from pathlib import Path


class TestE2EManual:
    """E2Eテスト（手動確認用）"""

    @pytest.mark.e2e
    def test_generate_sample_pptx(self, sample_ai_output, tmp_path):
        """サンプルPPTX生成"""
        from layout_engine import process_layout
        from pptx_builder import build_pptx

        layout_data = process_layout(sample_ai_output)
        pptx_bytes = build_pptx(layout_data)

        # 一時ファイルに保存
        output_path = tmp_path / "test_output.pptx"
        with open(output_path, "wb") as f:
            f.write(pptx_bytes)

        assert output_path.exists()
        print(f"\nGenerated: {output_path}")

    @pytest.mark.e2e
    def test_generate_all_templates(self, sample_ai_output, tmp_path):
        """全テンプレートで生成"""
        from layout_engine import process_layout
        from pptx_builder import build_pptx

        for template_id in ["T1", "T2", "T3", "T4"]:
            sample_ai_output["recommended_template"] = template_id
            layout_data = process_layout(sample_ai_output)
            pptx_bytes = build_pptx(layout_data)

            output_path = tmp_path / f"test_{template_id}.pptx"
            with open(output_path, "wb") as f:
                f.write(pptx_bytes)

            print(f"Generated: {output_path}")
```

---

## 5. パフォーマンス計測

### test_performance.py

```python
"""
Performance Tests
"""

import pytest
import time


class TestPerformance:
    """パフォーマンステスト"""

    @pytest.mark.performance
    def test_layout_processing_time(self, sample_ai_output):
        """レイアウト処理時間"""
        from layout_engine import process_layout

        start = time.time()
        for _ in range(100):
            process_layout(sample_ai_output)
        elapsed = time.time() - start

        avg_time = elapsed / 100
        print(f"\nLayout processing: {avg_time*1000:.2f}ms average")
        assert avg_time < 0.1  # 100ms以内

    @pytest.mark.performance
    def test_pptx_generation_time(self, sample_layout_data):
        """PPTX生成時間"""
        from pptx_builder import build_pptx

        start = time.time()
        for _ in range(10):
            build_pptx(sample_layout_data)
        elapsed = time.time() - start

        avg_time = elapsed / 10
        print(f"\nPPTX generation: {avg_time*1000:.2f}ms average")
        assert avg_time < 2.0  # 2秒以内

    @pytest.mark.performance
    def test_full_pipeline_time(self, sample_ai_output):
        """フルパイプライン時間（AI除く）"""
        from layout_engine import process_layout
        from pptx_builder import build_pptx

        start = time.time()
        layout_data = process_layout(sample_ai_output)
        pptx_bytes = build_pptx(layout_data)
        elapsed = time.time() - start

        print(f"\nFull pipeline (no AI): {elapsed*1000:.2f}ms")
        assert elapsed < 3.0  # 3秒以内
```

---

## 6. 品質チェックリスト

### 生成品質チェック

- [ ] タイトルが正しく表示される
- [ ] 全セクションが表示される
- [ ] セクション見出しのアクセントバーが表示される
- [ ] 箇条書きが正しくフォーマットされる
- [ ] 表のヘッダーが青背景になる
- [ ] フローチャートの矢印が表示される
- [ ] 文字が切れていない（Auto-Shrink動作）

### レイアウト精度チェック

- [ ] 文字被りがない
- [ ] 図形ズレがない
- [ ] 余白が統一されている
- [ ] カラム間隔が正しい
- [ ] ヘッダー・フッターの位置が正しい

### デザイン一貫性チェック

- [ ] フォントがメイリオ
- [ ] 色がカラーパレットに準拠
- [ ] フォントサイズが仕様通り

### テスト実行コマンド

```bash
# 全テスト
pytest

# ユニットテストのみ
pytest tests/test_*.py -m "not integration and not e2e and not performance"

# 統合テスト
pytest -m integration

# E2Eテスト（PPTX生成）
pytest -m e2e -v

# パフォーマンステスト
pytest -m performance -v

# カバレッジ付き
pytest --cov=src --cov-report=html
```
