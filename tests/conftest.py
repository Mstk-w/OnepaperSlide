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
