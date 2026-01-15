import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from .base import AIProvider

# 既存のai_service.pyからロジックを流用するため、簡易的に定義
SYSTEM_PROMPT = """あなたは公務員向け資料作成の専門家です。
入力されたメモを分析し、A3横1枚の資料に最適な構造化JSONを生成してください。

## 出力形式
{
  "recommended_template": "T1" | "T2" | "T3" | "T4",
  "title": "資料タイトル（30文字以内）",
  "subtitle": "サブタイトル（省略可）",
  "sections": [
    {
      "id": "section_1",
      "column": 0,
      "header": "セクション見出し",
      "type": "bullets" | "table" | "flowchart" | "kpi_box" | "text_block",
      "content": {}
    }
  ],
  "footer_note": "補足情報"
}

注意事項:
- 各セクションの文章は端的でわかりやすい短文にすること
- 箇条書きは1項目あたり30文字以内
- フローチャートのステップは5個以内
- 表の列数は5列以内
"""

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            logging.error(f"Gemini configuration failed: {e}")

    def get_models(self) -> List[str]:
        try:
            all_models = genai.list_models()
            available_models = []
            for m in all_models:
                if "generateContent" in m.supported_generation_methods:
                    model_name = m.name.replace("models/", "")
                    available_models.append(model_name)
            available_models.sort(reverse=True)
            return available_models
        except Exception as e:
            logging.warning(f"Failed to list Gemini models: {e}")
            return []

    def generate_structured_content(self, text: str, model: str, template_id: Optional[str] = None) -> Dict[str, Any]:
        
        # モデル名の調整（gemini-1.5-flash 等はそのままでOKだが、エイリアス対応が必要ならここで行う）
        model_name = model 
        
        try:
            genai_model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.95,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                },
                system_instruction=SYSTEM_PROMPT
            )
            
            prompt_parts = []
            if template_id:
                prompt_parts.append(f"\n## テンプレート指定\nテンプレート「{template_id}」を使用してください。")
            prompt_parts.append(f"\n## 入力メモ\n\n{text}\n\n上記を構造化JSONで出力してください。")
            prompt = "\n".join(prompt_parts)

            response = genai_model.generate_content(prompt)
            
            # JSONパース（ai_service.pyのロジックを流用・簡略化）
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                # 簡易的なコードブロック抽出
                match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response.text)
                if match:
                    return json.loads(match.group(1).strip())
                # 波括弧抽出
                match = re.search(r'\{[\s\S]*\}', response.text)
                if match:
                    return json.loads(match.group())
                raise ValueError("Failed to parse JSON")

        except Exception as e:
            logging.error(f"Gemini generation error: {e}")
            raise e
