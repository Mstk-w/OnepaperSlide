import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from .base import AIProvider

# 既存のai_service.pyからロジックを流用するため、簡易的に定義
SYSTEM_PROMPT = """あなたは「戦略コンサルタント」かつ「熟練した公務員」の視点を持つ、資料作成のプロフェッショナルです。
入力されたメモを分析し、上司や決裁者を「説得」するために最適なA3横1枚の資料構成（構造化JSON）を生成してください。

## 思考プロセス (Chain of Thought)
1.  **目的の明確化**: この資料は何を決裁してもらうためのものか？（予算獲得？ 施策承認？ 業務改善？）
2.  **論理構成 (Logic)**:
    - 現状 (As-Is) と あるべき姿 (To-Be) のギャップは何か？
    - なぜその施策が必要なのか？ (Why)
    - その効果は定量的・定性的にどう示せるか？ (Evidence)
3.  **リスク対策**: 予想される反論は何か？それに対する対策は？

## 出力ガイドライン
- **説得力を最優先**: 単なる要約ではなく、行間を読んで「補足」や「強調」を行い、説得力を高めること。
- **強調**: 重要なキーワードやインパクトのある数値は、必ず `**` で囲んで強調する（例: `**30%削減**`）。
- **具体性**: "効率化する" ではなく "作業時間を約xx%削減し、コア業務への注力を可能にする" のように具体的に記述する。
- **プレースホルダー**: 明確な数値がない場合は `[要確認: 削減コストの目安]` のようにユーザーが後で埋めるべき箇所を明示する。
- **文字数**:
    - 過度な短縮は禁止。文意が伝わる十分な長さを確保すること（1項目 50〜100文字程度も可）。
    - 専門用語には必要に応じて注釈を加える感覚で。

## 出力形式 (JSON)
{
  "recommended_template": "T1" | "T2" | "T3" | "T4",
  "title": "資料タイトル（具体的かつ魅力的・30文字以内）",
  "subtitle": "サブタイトル（目的やゴールを簡潔に）",
  "sections": [
    {
      "id": "section_1",
      "column": 0, // 0:左カラム, 1:右カラム
      "header": "セクション見出し（例: 現状の課題とボトルネック）",
      "type": "bullets" | "table" | "flowchart" | "kpi_box" | "text_block",
      "content": {
        // type=bulletsの場合
        "items": [
           { "text": "項目本文", "indent": 0 },
           { "text": "補足説明や根拠データ", "indent": 1 }
        ],
         // type=text_blockの場合
        "text": "詳細な説明文...",
        
        // type=kpi_boxの場合
        "value": "30%", "unit": "削減", "label": "残業時間",
        
        // type=flowchartの場合
        "steps": ["Step1", "Step2..."],
        
        // type=tableの場合
        "columns": ["項目", "現状", "改善後"],
        "rows": [["コスト", "100万円", "50万円"]]
      }
    }
  ],
  "footer_note": "補足情報・出典・作成日など"
}"""

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
