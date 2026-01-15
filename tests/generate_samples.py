
import sys
import os
from pathlib import Path
from io import BytesIO

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from layout_engine import process_layout
from pptx_builder import build_pptx
from logging_config import setup_logging

setup_logging()

def generate_sample(template_id: str, title: str, sections: list) -> Path:
    """サンプルスライドを生成"""
    
    mock_data = {
        "recommended_template": template_id,
        "title": title,
        "subtitle": f"テンプレート {template_id} 自動生成サンプル",
        "sections": sections,
        "footer_note": "Confidential - Internal Use Only"
    }
    
    print(f"Generating sample for {template_id}...")
    layout_data = process_layout(mock_data)
    pptx_stream = build_pptx(layout_data)
    
    output_dir = Path("output/samples")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"sample_{template_id}.pptx"
    output_path = output_dir / filename
    
    with open(output_path, "wb") as f:
        f.write(pptx_stream.getvalue())
        
    print(f"Saved: {output_path}")
    return output_path

def main():
    # T1: 問題解決型
    generate_sample(
        "T1",
        "オンライン申請システム導入による業務効率化",
        [
            {
                "id": "s1", "header": "現状分析", "type": "bullets", "column": 0,
                "content": {"items": ["紙ベースの申請が月間500件発生", "職員による手入力処理に時間がかかる", "書類の紛失リスクがある"]}
            },
            {
                "id": "s2", "header": "課題", "type": "kpi_box", "column": 0,
                "content": {"value": "30", "unit": "分/件", "label": "処理時間"}
            },
            {
                "id": "s3", "header": "原因分析", "type": "text_block", "column": 0,
                "content": {"text": "レガシーな業務フローが踏襲されており、デジタル化への移行コスト（学習コスト含む）が障壁となっている。また、既存システムとの連携機能が不足している。"}
            },
            {
                "id": "s4", "header": "解決策", "type": "flowchart", "column": 1,
                "content": {"steps": ["現状調査", "要件定義", "システム導入", "運用開始"], "direction": "h"}
            },
            {
                "id": "s5", "header": "期待効果", "type": "bullets", "column": 1,
                "content": {"items": ["処理時間の50%削減", "ペーパーレス化によるコスト削減", "申請者の利便性向上", "転記ミスの撲滅"]}
            }
        ]
    )

    # T2: 比較検討型
    generate_sample(
        "T2",
        "庁内チャットツール導入における比較検討",
        [
            {
                "id": "s1", "header": "比較背景", "type": "text_block", "column": 0,
                "content": {"text": "メールによるコミュニケーションの非効率性を解消するため、チャットツールの導入を検討する。セキュリティ、コスト、使いやすさの観点から3つの候補を比較する。"}
            },
            {
                "id": "s2", "header": "比較表", "type": "table", "column": 0,
                "content": {
                    "columns": ["項目", "製品A", "製品B", "製品C"],
                    "rows": [
                        ["コスト", "高い", "普通", "安い"],
                        ["機能", "多機能", "バランス", "シンプル"],
                        ["セキュリティ", "高", "中", "低"]
                    ]
                }
            },
            {
                "id": "s3", "header": "推奨案", "type": "kpi_box", "column": 1,
                "content": {"value": "製品B", "unit": "", "label": "推奨"}
            },
            {
                "id": "s4", "header": "選定理由", "type": "bullets", "column": 1,
                "content": {"items": ["コストと機能のバランスが最も良い", "既存システムとの連携が容易", "自治体での導入実績が豊富"]}
            }
        ]
    )

    # T3: 施策提案型
    generate_sample(
        "T3",
        "地域観光振興プロジェクト案",
        [
            {
                "id": "s1", "header": "背景と目的", "type": "bullets", "column": 0,
                "content": {"items": ["インバウンド需要の回復", "地域経済の活性化", "文化財の保存と活用"]}
            },
            {
                "id": "s2", "header": "ターゲット", "type": "text_block", "column": 0,
                "content": {"text": "主に20代〜30代の個人旅行客をターゲットとし、SNS映えするスポットや体験型コンテンツを強化する。"}
            },
            {
                "id": "s3", "header": "施策概要", "type": "flowchart", "column": 1,
                "content": {"steps": ["資源発掘", "プロモーション", "受入環境整備", "効果測定"], "direction": "v"}
            },
            {
                "id": "s4", "header": "予算計画", "type": "table", "column": 1,
                "content": {
                    "columns": ["項目", "金額（千円）"],
                    "rows": [
                        ["調査費", "1,000"],
                        ["広告費", "3,000"],
                        ["イベント費", "2,000"]
                    ]
                }
            }
        ]
    )

    # T4: 業務フロー型
    generate_sample(
        "T4",
        "経費精算業務プロセスの改善",
        [
            {
                "id": "s1", "header": "現状フロー", "type": "flowchart", "column": 0,
                "content": {"steps": ["申請書作成", "上長承認", "経理確認", "精算実行"], "direction": "v"}
            },
            {
                "id": "s2", "header": "問題点", "type": "bullets", "column": 0,
                "content": {"items": ["承認待ち時間が長い", "差し戻しが多い", "紙の保管コスト"]}
            },
            {
                "id": "s3", "header": "改善後フロー", "type": "flowchart", "column": 1,
                "content": {"steps": ["システム入力", "自動チェック", "電子承認", "振込"], "direction": "v"}
            },
             {
                "id": "s4", "header": "改善効果", "type": "text_block", "column": 1,
                "content": {"text": "システム化により、申請から精算までのリードタイムを平均5日から2日に短縮。ペーパーレス化により年間10万円の保管コストを削減。"}
            }
        ]
    )

if __name__ == "__main__":
    main()
