import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .base import AIProvider

SYSTEM_PROMPT = """あなたは公務員向け資料作成の専門家です。
入力されたメモを分析し、A3横1枚の資料に最適な構造化JSONを生成してください。
出力は必ず純粋なJSON形式で行ってください。コードブロックは不要です。

出力形式JSONスキーマ:
{
  "recommended_template": "T1" | "T2" | "T3" | "T4",
  "title": "資料タイトル",
  "subtitle": "サブタイトル",
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
"""

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def get_models(self) -> List[str]:
        # OpenAIはモデル一覧APIがあるが、chatモデル以外も含まれるため
        # ここでは主要なモデルをハードコードするか、フィルタリングして返す
        # ユーザー体験を考慮し、推奨モデルを返す形が一般的だが、一応取得を試みる
        try:
            models = self.client.models.list()
            chat_models = [m.id for m in models.data if "gpt" in m.id]
            chat_models.sort(reverse=True)
            return chat_models
        except Exception as e:
            logging.warning(f"Failed to list OpenAI models: {e}")
            # フォールバック
            return ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]

    def generate_structured_content(self, text: str, model: str, template_id: Optional[str] = None) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"テンプレート指定: {template_id}" if template_id else ""},
            {"role": "user", "content": f"入力メモ:\n{text}"}
        ]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logging.error(f"OpenAI generation error: {e}")
            raise e
