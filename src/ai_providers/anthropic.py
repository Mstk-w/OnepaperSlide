import json
import logging
import re
from typing import List, Dict, Any, Optional
import anthropic
from .base import AIProvider

SYSTEM_PROMPT = """あなたは公務員向け資料作成の専門家です。
入力されたメモを分析し、A3横1枚の資料に最適な構造化JSONを生成してください。
出力はJSONのみを行ってください。

出力形式:
{
  "recommended_template": "T1" | "T2" | "T3" | "T4",
  "title": "資料タイトル",
  "sections": [...]
}
"""

class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def get_models(self) -> List[str]:
        # Anthropic API doesn't have a public 'list models' endpoint that is easy to use for all users yet in the same way
        # But we can return the known supported models
        return [
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]

    def generate_structured_content(self, text: str, model: str, template_id: Optional[str] = None) -> Dict[str, Any]:
        prompt = f"{text}\n\nテンプレート指定: {template_id}" if template_id else text
        
        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=0.3,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "{"} # JSON出力を強制するためのプリフィル
                ]
            )
            
            # プリフィルした '{' を補ってパース
            content = "{" + message.content[0].text
            
            # 簡易的なJSON抽出
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 頑張って抽出
                match = re.search(r'\{[\s\S]*\}', content)
                if match:
                    return json.loads(match.group())
                raise ValueError("Failed to parse JSON from Anthropic response")

        except Exception as e:
            logging.error(f"Anthropic generation error: {e}")
            raise e
