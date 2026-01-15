import os
import logging
import time
from typing import Dict, Any, cast, List

# AIプロバイダー
from ai_providers.base import AIProvider
from ai_providers.gemini import GeminiProvider
from ai_providers.openai import OpenAIProvider
from ai_providers.anthropic import AnthropicProvider
from content_processor import post_process_content

from custom_types import AIOutput

# ロガー設定
logger = logging.getLogger("ai_service")

class AIServiceError(Exception):
    """AIサービス関連のエラー"""
    pass

def get_provider_type(api_key: str) -> str:
    """APIキーからプロバイダータイプを判定"""
    if not api_key:
        return "gemini"
    
    if api_key.startswith("sk-ant-"):
        return "anthropic"
    elif api_key.startswith("sk-"):
        return "openai"
    elif api_key.startswith("AIza"):
        return "gemini"
    else:
        # デフォルトはGemini（あるいはエラーにする方針も可）
        return "gemini"

def get_provider(api_key: str) -> AIProvider:
    """プロバイダーインスタンスを取得"""
    provider_type = get_provider_type(api_key)
    
    if provider_type == "anthropic":
        return AnthropicProvider(api_key)
    elif provider_type == "openai":
        return OpenAIProvider(api_key)
    else:
        return GeminiProvider(api_key)

def get_available_models(api_key: str = None) -> List[str]:
    """利用可能なモデル一覧を取得"""
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    
    if not key:
        return []
        
    try:
        provider = get_provider(key)
        return provider.get_models()
    except Exception as e:
        logger.warning(f"Failed to list models: {e}")
        return []

def generate_structured_content(
    memo_text: str,
    model: str = "gemini-2.0-flash",
    template_id: str = None,
    api_key: str = None,
    max_retries: int = 3
) -> AIOutput:
    """
    メモテキストを構造化データに変換
    """
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise AIServiceError("API key is required")

    provider = get_provider(key)
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Generating content with {provider.__class__.__name__} (Model: {model})...")
            
            data = provider.generate_structured_content(memo_text, model, template_id)
            
            # コンテンツ後処理（文字数制限や項目数調整）
            # 各プロバイダーがraw dictを返すので、ここで共通の後処理を挟む
            data = post_process_content(data)
            
            return cast(AIOutput, data)
            
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                
    raise AIServiceError(f"Failed to generate content after {max_retries} attempts: {last_error}")


