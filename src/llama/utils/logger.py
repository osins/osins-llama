"""日志管理工具"""
from pathlib import Path
import sys
from llama.core.logger_manager import LoggerManager


def setup_logger(
    name: str = "app_logger",
    log_file: str = None,
    debug: bool = False,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
):
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        debug: 是否启用调试模式
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的备份文件数量

    Returns:
        LoggerManager: 配置好的日志记录器
    """
    logger = LoggerManager(name=name, debug=debug, log_to_console=True)
    
    # 注意：由于LoggerManager是单例模式，如果需要特定的日志文件处理，
    # 可能需要扩展LoggerManager以支持文件处理
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # 这里可以扩展LoggerManager以支持文件日志
        # 目前只使用控制台输出，如需文件日志功能，请扩展LoggerManager
    
    return logger