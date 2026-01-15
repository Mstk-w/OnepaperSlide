"""
AI Service Unit Tests
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_service import (
    parse_response,
    validate_output,
    fix_output,
    build_prompt,
    suggest_template,
    AIServiceError
)


class TestParseResponse:
    """JSON解析のテスト"""

    def test_parse_valid_json(self):
        """有効なJSONをパース"""
        json_str = '{"title": "Test", "sections": [], "recommended_template": "T1"}'
        result = parse_response(json_str)
        assert result["title"] == "Test"

    def test_parse_json_in_code_block(self):
        """コードブロック内のJSONをパース"""
        response = '''
        Here is the result:
        ```json
        {"title": "Test", "sections": [], "recommended_template": "T1"}
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
        data = {"recommended_template": "T1", "sections": [{"id": "s1", "type": "bullets"}]}
        is_valid, error = validate_output(data)
        assert is_valid is False
        assert "title" in error

    def test_invalid_template(self):
        """無効なテンプレート"""
        data = {
            "recommended_template": "T99",
            "title": "Test",
            "sections": [{"id": "s1", "type": "bullets"}]
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


class TestSuggestTemplate:
    """テンプレート推定のテスト"""

    def test_suggest_t4_for_flow(self):
        """フロー関連でT4を推定"""
        text = "業務フローを改善したい"
        result = suggest_template(text)
        assert result == "T4"

    def test_suggest_t2_for_comparison(self):
        """比較関連でT2を推定"""
        text = "案Aと案Bを比較検討する"
        result = suggest_template(text)
        assert result == "T2"

    def test_suggest_t1_as_default(self):
        """デフォルトでT1を推定"""
        text = "課題を解決したい"
        result = suggest_template(text)
        assert result == "T1"
