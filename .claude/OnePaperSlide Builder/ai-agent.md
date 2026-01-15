# AI-Agent: Gemini API連携ガイド

## 担当ファイル

- `src/ai_service.py` - Gemini API連携モジュール

## 目次

1. [API初期化](#1-api初期化)
2. [構造化プロンプト](#2-構造化プロンプト)
3. [JSON応答パース](#3-json応答パース)
4. [エラーリトライ](#4-エラーリトライ)
5. [テンプレート自動選択](#5-テンプレート自動選択)
6. [完全実装例](#6-完全実装例)

---

## 1. API初期化

### インストール

```bash
pip install google-generativeai
```

### 初期化コード

```python
import google.generativeai as genai
import os

def initialize_gemini(api_key: str = None) -> genai.GenerativeModel:
    """Gemini APIを初期化"""

    # APIキー取得（引数優先、なければ環境変数）
    key = api_key or os.environ.get("GEMINI_API_KEY")

    if not key:
        raise ValueError("GEMINI_API_KEY is not set")

    genai.configure(api_key=key)

    # モデル設定
    generation_config = {
        "temperature": 0.3,      # 安定した出力のため低めに
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json"  # JSON出力を強制
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config
    )

    return model
```

### モデル選択

```python
def get_model(model_name: str = "gemini-2.0-flash") -> genai.GenerativeModel:
    """指定されたモデルを取得"""

    model_map = {
        "gemini-2.0-flash": "gemini-2.0-flash",
        "gemini-2.0-pro": "gemini-2.0-pro",
        # 旧バージョン互換
        "flash": "gemini-2.0-flash",
        "pro": "gemini-2.0-pro"
    }

    model_id = model_map.get(model_name, "gemini-2.0-flash")

    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json"
    }

    return genai.GenerativeModel(
        model_name=model_id,
        generation_config=generation_config
    )
```

---

## 2. 構造化プロンプト

### システムプロンプト

```python
SYSTEM_PROMPT = """あなたは公務員向け資料作成の専門家です。
入力されたメモを分析し、A3横1枚の資料に最適な構造化JSONを生成してください。

## 出力形式

以下のJSON形式で出力してください。必ずこの形式に従ってください。

```json
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
      "content": {
        // 型に応じた構造化データ（後述）
      }
    }
  ],
  "footer_note": "補足情報・連絡先（省略可）"
}
```

## テンプレート選択基準

- **T1（問題解決型）**: 課題→原因→解決策→効果の流れがある場合
- **T2（比較検討型）**: 複数の選択肢を比較する場合
- **T3（施策提案型）**: 新規施策・プロジェクトの説明の場合
- **T4（業務フロー型）**: プロセス・手順の改善を扱う場合

## コンテンツタイプ別の構造

### bullets（箇条書き）
```json
{
  "items": ["項目1", "項目2", "項目3"]
}
```

### table（表）
```json
{
  "columns": ["列1", "列2", "列3"],
  "rows": [
    ["データ1-1", "データ1-2", "データ1-3"],
    ["データ2-1", "データ2-2", "データ2-3"]
  ]
}
```

### flowchart（フローチャート）
```json
{
  "steps": ["ステップ1", "ステップ2", "ステップ3"],
  "direction": "h"
}
```
- direction: "h"（横配置）または "v"（縦配置）

### kpi_box（数値強調）
```json
{
  "value": "50",
  "unit": "%",
  "label": "削減率"
}
```

### text_block（テキスト）
```json
{
  "text": "説明文テキスト"
}
```

## セクション配置ルール

- column: 0（左列）または 1（右列）
- 左列に2-3セクション、右列に2-3セクションを配置
- セクション数は合計4-6個が理想

## 品質基準

- 各セクションの文章は端的でわかりやすい短文にすること
- 箇条書きは1項目あたり30文字以内
- フローチャートのステップは5個以内
- 表の列数は5列以内
- タイトルは具体的かつ簡潔に（「〇〇について」は避ける）
"""
```

### プロンプト構築

```python
def build_prompt(
    memo_text: str,
    template_id: str = None
) -> str:
    """プロンプトを構築"""

    prompt_parts = [SYSTEM_PROMPT]

    # テンプレート指定がある場合
    if template_id:
        prompt_parts.append(f"""
## テンプレート指定

ユーザーがテンプレート「{template_id}」を指定しました。
このテンプレートに適した構成でセクションを作成してください。
""")

    # ユーザー入力
    prompt_parts.append(f"""
## 入力メモ

以下のメモを構造化してください:

---
{memo_text}
---

上記のメモを分析し、指定されたJSON形式で出力してください。
""")

    return "\n".join(prompt_parts)
```

---

## 3. JSON応答パース

### 基本パース

```python
import json
import re

def parse_ai_response(response_text: str) -> dict:
    """AI応答からJSONを抽出・パース"""

    # 1. そのままパースを試みる
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # 2. コードブロックからJSONを抽出
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. 波括弧で囲まれた部分を抽出
    brace_match = re.search(r'\{[\s\S]*\}', response_text)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse JSON from response: {response_text[:200]}...")
```

### バリデーション

```python
from typing import Optional

def validate_ai_output(data: dict) -> tuple[bool, Optional[str]]:
    """AI出力のバリデーション"""

    # 必須フィールドチェック
    required_fields = ["recommended_template", "title", "sections"]
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"

    # テンプレートID検証
    valid_templates = ["T1", "T2", "T3", "T4"]
    if data["recommended_template"] not in valid_templates:
        return False, f"Invalid template: {data['recommended_template']}"

    # セクション検証
    sections = data.get("sections", [])
    if not sections:
        return False, "No sections found"

    if len(sections) > 8:
        return False, f"Too many sections: {len(sections)} (max 8)"

    for i, section in enumerate(sections):
        # 必須フィールド
        if "id" not in section:
            return False, f"Section {i}: missing 'id'"
        if "type" not in section:
            return False, f"Section {i}: missing 'type'"

        # タイプ検証
        valid_types = ["bullets", "table", "flowchart", "kpi_box", "text_block"]
        if section["type"] not in valid_types:
            return False, f"Section {i}: invalid type '{section['type']}'"

        # column検証
        column = section.get("column", 0)
        if column not in [0, 1]:
            return False, f"Section {i}: invalid column {column}"

    return True, None
```

### 自動修正

```python
def fix_ai_output(data: dict) -> dict:
    """AI出力の軽微な問題を自動修正"""

    # テンプレートIDの正規化
    template_map = {
        "t1": "T1", "T1_problem_solving": "T1", "問題解決型": "T1",
        "t2": "T2", "T2_comparison": "T2", "比較検討型": "T2",
        "t3": "T3", "T3_policy_proposal": "T3", "施策提案型": "T3",
        "t4": "T4", "T4_workflow": "T4", "業務フロー型": "T4"
    }

    template = data.get("recommended_template", "T1")
    data["recommended_template"] = template_map.get(template, template)

    # セクションIDの自動付与
    for i, section in enumerate(data.get("sections", [])):
        if "id" not in section:
            section["id"] = f"section_{i + 1}"

        # columnのデフォルト値
        if "column" not in section:
            section["column"] = 0 if i < len(data["sections"]) // 2 else 1

        # typeのデフォルト値
        if "type" not in section:
            section["type"] = "text_block"

        # contentの確保
        if "content" not in section:
            section["content"] = {}

    return data
```

---

## 4. エラーリトライ

```python
import time
from typing import Callable

class AIServiceError(Exception):
    """AI Service専用エラー"""
    pass

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """指数バックオフ付きリトライ"""

    last_error = None

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e

            # リトライ不可のエラー
            error_msg = str(e).lower()
            if "api_key" in error_msg or "authentication" in error_msg:
                raise AIServiceError(f"認証エラー: {e}")

            if "quota" in error_msg or "rate limit" in error_msg:
                # レート制限は長めに待機
                delay = initial_delay * (backoff_factor ** attempt) * 2
            else:
                delay = initial_delay * (backoff_factor ** attempt)

            if attempt < max_retries - 1:
                print(f"Retry {attempt + 1}/{max_retries} after {delay}s...")
                time.sleep(delay)

    raise AIServiceError(f"{max_retries}回のリトライ後も失敗: {last_error}")
```

### API呼び出しのラッパー

```python
def call_gemini_with_retry(
    model: genai.GenerativeModel,
    prompt: str,
    max_retries: int = 3
) -> str:
    """リトライ付きGemini API呼び出し"""

    def _call():
        response = model.generate_content(prompt)
        return response.text

    return retry_with_backoff(_call, max_retries=max_retries)
```

---

## 5. テンプレート自動選択

### キーワードベース選択

```python
def suggest_template(memo_text: str) -> str:
    """メモ内容からテンプレートを推定（フォールバック用）"""

    text_lower = memo_text.lower()

    # T4: 業務フロー型
    flow_keywords = ["フロー", "手順", "ステップ", "プロセス", "流れ", "工程"]
    if any(kw in text_lower for kw in flow_keywords):
        return "T4"

    # T2: 比較検討型
    compare_keywords = ["比較", "案a", "案b", "選択肢", "メリット", "デメリット", "オプション"]
    if any(kw in text_lower for kw in compare_keywords):
        return "T2"

    # T3: 施策提案型
    proposal_keywords = ["施策", "プロジェクト", "計画", "予算", "スケジュール", "新規"]
    if any(kw in text_lower for kw in proposal_keywords):
        return "T3"

    # T1: 問題解決型（デフォルト）
    return "T1"
```

---

## 6. 完全実装例

### ai_service.py

```python
"""
OnePaperSlide AI Service
Gemini APIを使用したテキスト構造化
"""

import google.generativeai as genai
import json
import re
import time
import os
from typing import Optional, Dict, Any


class AIServiceError(Exception):
    """AI Service専用エラー"""
    pass


# システムプロンプト
SYSTEM_PROMPT = """あなたは公務員向け資料作成の専門家です。
入力されたメモを分析し、A3横1枚の資料に最適な構造化JSONを生成してください。

## 出力形式

以下のJSON形式で出力してください。必ずこの形式に従ってください。

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
  "footer_note": "補足情報（省略可）"
}

## テンプレート選択基準

- T1（問題解決型）: 課題→原因→解決策→効果の流れ
- T2（比較検討型）: 複数選択肢の比較
- T3（施策提案型）: 新規施策・プロジェクト説明
- T4（業務フロー型）: プロセス改善

## コンテンツタイプ

- bullets: {"items": ["項目1", "項目2"]}
- table: {"columns": ["列1", "列2"], "rows": [["値1", "値2"]]}
- flowchart: {"steps": ["手順1", "手順2"], "direction": "h"}
- kpi_box: {"value": "50", "unit": "%", "label": "削減率"}
- text_block: {"text": "説明文"}

## 品質基準

- 箇条書き: 1項目30文字以内
- フローチャート: 5ステップ以内
- 表: 5列以内
- セクション: 4-6個
"""


def initialize_gemini(api_key: str = None) -> None:
    """Gemini APIを初期化"""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise AIServiceError("GEMINI_API_KEY is not set")
    genai.configure(api_key=key)


def get_model(model_name: str = "gemini-2.0-flash") -> genai.GenerativeModel:
    """モデルを取得"""
    model_map = {
        "gemini-2.0-flash": "gemini-2.0-flash",
        "gemini-2.0-pro": "gemini-2.0-pro",
        "flash": "gemini-2.0-flash",
        "pro": "gemini-2.0-pro"
    }

    model_id = model_map.get(model_name, "gemini-2.0-flash")

    return genai.GenerativeModel(
        model_name=model_id,
        generation_config={
            "temperature": 0.3,
            "top_p": 0.95,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json"
        }
    )


def build_prompt(memo_text: str, template_id: str = None) -> str:
    """プロンプトを構築"""
    parts = [SYSTEM_PROMPT]

    if template_id:
        parts.append(f"\n## テンプレート指定\nテンプレート「{template_id}」を使用してください。")

    parts.append(f"\n## 入力メモ\n\n{memo_text}\n\n上記を構造化JSONで出力してください。")

    return "\n".join(parts)


def parse_response(response_text: str) -> dict:
    """AI応答をパース"""
    # 直接パース
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # コードブロック抽出
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 波括弧抽出
    match = re.search(r'\{[\s\S]*\}', response_text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise AIServiceError(f"JSON解析失敗: {response_text[:200]}...")


def validate_output(data: dict) -> tuple[bool, Optional[str]]:
    """出力をバリデーション"""
    required = ["recommended_template", "title", "sections"]
    for field in required:
        if field not in data:
            return False, f"Missing: {field}"

    if data["recommended_template"] not in ["T1", "T2", "T3", "T4"]:
        return False, f"Invalid template: {data['recommended_template']}"

    sections = data.get("sections", [])
    if not sections or len(sections) > 8:
        return False, f"Invalid section count: {len(sections)}"

    return True, None


def fix_output(data: dict) -> dict:
    """出力を自動修正"""
    # テンプレートID正規化
    template_map = {
        "t1": "T1", "T1_problem_solving": "T1",
        "t2": "T2", "T2_comparison": "T2",
        "t3": "T3", "T3_policy_proposal": "T3",
        "t4": "T4", "T4_workflow": "T4"
    }
    template = data.get("recommended_template", "T1")
    data["recommended_template"] = template_map.get(template, template)

    # セクション修正
    for i, section in enumerate(data.get("sections", [])):
        if "id" not in section:
            section["id"] = f"section_{i + 1}"
        if "column" not in section:
            section["column"] = 0 if i < len(data["sections"]) // 2 else 1
        if "type" not in section:
            section["type"] = "text_block"
        if "content" not in section:
            section["content"] = {}

    return data


def generate_structured_content(
    memo_text: str,
    model: str = "gemini-2.0-flash",
    template_id: str = None,
    api_key: str = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    メモテキストを構造化データに変換

    Args:
        memo_text: 入力テキスト
        model: 使用するモデル名
        template_id: テンプレートID（指定時は固定）
        api_key: APIキー（省略時は環境変数）
        max_retries: 最大リトライ回数

    Returns:
        構造化されたJSONデータ
    """
    # 初期化
    initialize_gemini(api_key)
    gemini_model = get_model(model)

    # プロンプト構築
    prompt = build_prompt(memo_text, template_id)

    # リトライ付き呼び出し
    last_error = None
    for attempt in range(max_retries):
        try:
            # API呼び出し
            response = gemini_model.generate_content(prompt)
            response_text = response.text

            # パース
            data = parse_response(response_text)

            # 修正
            data = fix_output(data)

            # バリデーション
            is_valid, error_msg = validate_output(data)
            if not is_valid:
                raise AIServiceError(f"バリデーション失敗: {error_msg}")

            return data

        except Exception as e:
            last_error = e
            error_msg = str(e).lower()

            # リトライ不可エラー
            if "api_key" in error_msg or "authentication" in error_msg:
                raise AIServiceError(f"認証エラー: {e}")

            # リトライ
            if attempt < max_retries - 1:
                delay = 1.0 * (2 ** attempt)
                if "quota" in error_msg or "rate" in error_msg:
                    delay *= 2
                time.sleep(delay)

    raise AIServiceError(f"リトライ上限到達: {last_error}")
```

---

## エラーメッセージ一覧

| エラー | 原因 | 対処 |
|--------|------|------|
| `GEMINI_API_KEY is not set` | APIキー未設定 | 環境変数またはsecrets.tomlを設定 |
| `認証エラー` | APIキー無効 | APIキーを再確認 |
| `JSON解析失敗` | AI応答が不正 | リトライまたはプロンプト調整 |
| `バリデーション失敗` | 構造が不正 | 修正ロジックを追加 |
| `リトライ上限到達` | 連続エラー | API状態を確認 |
