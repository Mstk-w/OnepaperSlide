from typing import List, Dict, Any
from logging_config import get_logger

logger = get_logger("content_processor")

def truncate_text(text: str, max_length: int = 100) -> str:
    """指定文字数でテキストを切り詰め、末尾に...を付与"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def process_bullets(items: List[Any], max_items: int = 7, max_length: int = 50) -> List[Dict[str, Any]]:
    """箇条書きの項目数と長さを制限"""
    processed = []
    for i, item in enumerate(items):
        if i >= max_items:
            break
        
        # 文字列または辞オオブジェクトに対応
        if isinstance(item, str):
            text = item
            indent = 0
        else:
            text = item.get("text", "")
            indent = item.get("indent", 0)
            
        processed.append({
            "text": truncate_text(text, max_length),
            "indent": indent
        })
    
    if len(items) > max_items:
        logger.info(f"Bullets truncated: original {len(items)} -> {max_items}")
        
    return processed

def process_flowchart_steps(steps: List[Any], max_steps: int = 6) -> List[Any]:
    """フローチャートのステップ数を制限"""
    if len(steps) <= max_steps:
        return steps
        
    logger.info(f"Flowchart steps truncated: original {len(steps)} -> {max_steps}")
    return steps[:max_steps]

def post_process_content(ai_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI出力データの全体的な後処理
    
    各セクションのコンテンツに対して、レイアウト崩れを防ぐための
    制限（文字数、項目数など）を適用する。
    """
    logger.info("Starting content post-processing")
    processed_output = ai_output.copy()
    sections = processed_output.get("sections", [])
    processed_sections = []
    
    for section in sections:
        sec_type = section.get("type")
        content = section.get("content", {})
        
        if sec_type == "bullets":
            items = content.get("items", [])
            content["items"] = process_bullets(items)
            
        elif sec_type == "flowchart":
            steps = content.get("steps", [])
            content["steps"] = process_flowchart_steps(steps)
            
        elif sec_type == "text_block":
            text = content.get("text", "")
            if isinstance(text, str):
                content["text"] = truncate_text(text, max_length=200)
                
        section["content"] = content
        processed_sections.append(section)
        
    processed_output["sections"] = processed_sections
    logger.info("Content post-processing completed")
    return processed_output
