from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class AIProvider(ABC):
    """AIプロバイダーの基底クラス"""

    @abstractmethod
    def get_models(self) -> List[str]:
        """利用可能なモデル一覧を取得"""
        pass

    @abstractmethod
    def generate_structured_content(self, text: str, model: str, template_id: Optional[str] = None) -> Dict[str, Any]:
        """構造化されたコンテンツを生成"""
        pass
