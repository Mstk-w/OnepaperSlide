"""
OnePaperSlide 統合テスト
AIサービス（モック）、レイアウトエンジン、PPTXビルダーの連携をテスト
"""

import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
import json

from ai_service import generate_structured_content, AIServiceError
from layout_engine import process_layout
from pptx_builder import build_pptx
from custom_types import AIOutput

class TestIntegration:
    
    @patch("ai_service.GeminiClient")
    def test_full_pipeline_success(self, MockClient, sample_memo_text, sample_ai_output):
        """正常系：入力からPPTX生成までの完全なフロー"""
        
        # モックの設定
        mock_instance = MockClient.return_value
        mock_instance.generate.return_value = sample_ai_output
        
        # 1. AIサービス呼び出し
        ai_output = generate_structured_content(
            memo_text=sample_memo_text,
            api_key="dummy_key"
        )
        
        assert ai_output == sample_ai_output
        
        # 2. レイアウト処理
        layout_data = process_layout(ai_output)
        assert layout_data["template_id"] == "T1"
        assert len(layout_data["sections"]) == 4
        
        # 3. PPTX生成
        pptx_stream = build_pptx(layout_data)
        assert isinstance(pptx_stream, BytesIO)
        assert pptx_stream.getbuffer().nbytes > 0
        
    @patch("ai_service.GeminiClient")
    def test_pipeline_invalid_ai_response(self, MockClient, sample_memo_text):
        """異常系：AIが不正なデータを返した場合"""
        
        # モックの設定 - 必須フィールド欠落
        invalid_output = {"title": "No Sections"} 
        mock_instance = MockClient.return_value
        
        # GeminiClient.generate がバリデーションエラーを送出することをシミュレート
        # 実際にはGeminiClient内部でバリデーションを行いAIServiceErrorを出す
        mock_instance.generate.side_effect = AIServiceError("Invalid AI output")
        
        with pytest.raises(AIServiceError) as excinfo:
            generate_structured_content(sample_memo_text, api_key="dummy")
        
        assert "Invalid AI output" in str(excinfo.value)

    @patch("ai_service.GeminiClient")
    def test_pipeline_empty_input(self, MockClient, sample_ai_output):
        """エッジケース：空文字入力"""
        mock_instance = MockClient.return_value
        mock_instance.generate.return_value = sample_ai_output
        
        # 空文字でもエラーにならず（プロンプトに含まれる）、AIがよしなに返す想定
        # ただし、GeminiClient側で空文字チェックを入れるべきかは仕様次第
        # 現状の実装ではそのままAIに投げる
        
        result = generate_structured_content("", api_key="dummy")
        assert result == sample_ai_output

    @patch("ai_service.GeminiClient")
    def test_retry_mechanism(self, MockClient, sample_memo_text, sample_ai_output):
        """リトライメカニズムのテスト"""
        mock_instance = MockClient.return_value
        
        # 2回失敗して3回目に成功
        mock_instance.generate.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            sample_ai_output
        ]
        
        result = generate_structured_content(
            sample_memo_text, 
            api_key="dummy",
            max_retries=3
        )
        
        assert result == sample_ai_output
        # コンストラクタ呼び出し回数（リトライごとに再生成される実装の場合）
        # generate_structured_contentの実装ではループ内でGeminiClientを生成している
        assert MockClient.call_count == 3
        assert MockClient.call_count == 3

    @patch("ai_service.GeminiClient")
    def test_content_post_processing(self, MockClient, sample_memo_text):
        """Phase 5: コンテンツ後処理の検証"""
        
        # 長すぎるコンテンツを含むAI出力
        long_bullets = ["Item " + str(i) for i in range(20)] # 20項目（制限は7）
        long_text = "A" * 300 # 300文字（制限は100-200）
        
        raw_output: AIOutput = {
            "recommended_template": "T1",
            "title": "Long Content Test",
            "sections": [
                {
                    "id": "sec1", 
                    "type": "bullets", 
                    "column": 0, 
                    "header": "Bullets", 
                    "content": {"items": long_bullets}
                },
                {
                    "id": "sec2", 
                    "type": "text_block", 
                    "column": 1, 
                    "header": "Text", 
                    "content": {"text": long_text}
                }
            ]
        }
        
        mock_instance = MockClient.return_value
        mock_instance.generate.return_value = raw_output # generateは後処理前のデータを返すわけではないが、ここではモック動作として
        
        # 実際にはGeminiClient.generate内でpost_process_contentが呼ばれる
        # したがって、MockClient.generate自体はraw_outputを返すと設定しても、
        # post_process_contentが呼ばれるのはGeminiClientの実装内部。
        # ここではモック対象が`GeminiClient`全体なので、内部ロジック（post_process_content呼び出し）がスキップされてしまう。
        # 統合テストとしてはai_service.generate_structured_contentを呼ぶが、
        # 内部でGeminiClient(mock)を使うため、post_process_contentが呼ばれるか確認するには
        # GeminiClientの実装を一部生かすか、post_process_contentを個別にテストすべき。
        # ここでは、generate_structured_contentが返すものが加工されているかをテストしたいが、
        # GeminiClient全体をモックするとgenerateメソッドの実装もモックされるため、後処理が走らない。
        # よって、このテストは「ai_service.pyのgenerate_structured_content」ではなく
        # 「content_processor.py」の単体テスト、もしくはGeminiClientのgenerateメソッドのテストとして分離すべきだが、
        # ここでは簡易的に「post_process_content」が正しく機能することを別アプローチで確認する。
        
        from content_processor import post_process_content
        processed = post_process_content(raw_output)
        
        # 検証
        assert len(processed["sections"][0]["content"]["items"]) <= 7
        assert len(processed["sections"][1]["content"]["text"]) <= 203 # 200 + "..."

    def test_config_override(self):
        """Phase 5: デザイン設定オーバーライドの検証"""
        from config import config
        
        # 初期状態
        initial_primary = config.colors.primary
        
        # オーバーライド適用
        config.override_colors(primary="#FF0000", background="#000000")
        
        assert config.colors.primary == "#FF0000"
        assert config.colors.background == "#000000"
        
        # リセット
        config.reset_overrides()
        assert config.colors.primary == initial_primary
