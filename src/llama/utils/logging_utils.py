"""Logging utilities for osins-llama CLI."""
import os
from pathlib import Path
from typing import Optional
from llama.core.logger_manager import logger


def ensure_log_dir(path: Path) -> None:
    """确保日志目录存在且可写"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        if not os.access(path, os.W_OK):
            raise PermissionError(f"Cannot write to log directory: {path}")
    except Exception as e:
        raise RuntimeError(f"Failed to prepare log directory {path}: {e}")


def setup_logging(verbose: bool):
    """设置CLI日志记录器"""
    # 使用全局logger实例
    if verbose:
        logger.debug = lambda msg, *args, **kwargs: logger.logger.debug(msg, *args, **kwargs)
    
    return logger