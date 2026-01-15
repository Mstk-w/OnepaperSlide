"""
OnePaperSlide ロギング設定
アプリケーション全体で使用するロガーを設定
"""

import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    アプリケーションロガーを設定
    
    Args:
        level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    
    Returns:
        設定済みのルートロガー
    """
    # ログレベルのマッピング
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level = log_levels.get(level.upper(), logging.INFO)
    
    # フォーマット設定
    # 形式: [時刻] [レベル] [モジュール名] メッセージ
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # ルートロガー設定
    root_logger = logging.getLogger("onepaperslide")
    root_logger.setLevel(log_level)
    
    # 既存のハンドラーをクリア（重複防止）
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    
    # 伝播を無効化（重複ログ防止）
    root_logger.propagate = False
    
    return root_logger


def get_logger(module_name: str) -> logging.Logger:
    """
    モジュール用のロガーを取得
    
    Args:
        module_name: モジュール名（通常は __name__ を使用）
    
    Returns:
        モジュール用ロガー
    """
    return logging.getLogger(f"onepaperslide.{module_name}")
