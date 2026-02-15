"""Logging utilities for osins-llama CLI."""
import logging
import os
from pathlib import Path
from typing import Optional


def ensure_log_dir(path: Path) -> None:
    """确保日志目录存在且可写"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        if not os.access(path, os.W_OK):
            raise PermissionError(f"Cannot write to log directory: {path}")
    except Exception as e:
        raise RuntimeError(f"Failed to prepare log directory {path}: {e}")


def setup_logging(verbose: bool) -> logging.Logger:
    """设置CLI日志记录器"""
    logger = logging.getLogger("osins-llama.cli")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # 避免重复添加处理器
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # 添加文件处理器，便于审计
        try:
            log_dir = Path("/var/log/osins-llama")
            ensure_log_dir(log_dir)
            file_handler = logging.FileHandler(log_dir / "cli.log")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, RuntimeError) as e:
            # 如果无法创建日志文件，仅使用控制台输出并记录错误
            logger.warning(f"Could not create file logger: {e}")

    return logger