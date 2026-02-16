"""Stop command for osins-llama server."""
import click
import logging
import signal
import os
import sys
import time
from .pid_file_manager import PidFileManager
from .process import ProcessManager


def execute_stop(force: bool = False) -> int:
    """
    停止osins-llama服务器实例

    Args:
        force: 是否强制停止

    Returns:
        int: 返回码 (0: 成功, 1: 一般错误, 2: 超时)

    Raises:
        ValueError: 当PID文件路径无效时
        PermissionError: 当权限不足时
        ProcessLookupError: 当目标进程不存在时
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"Attempting to stop process, force={force}")

    # 使用 ProcessManager 来停止进程
    process_manager = ProcessManager(expected_cmd_keyword="llama.api.server")
    
    if force:
        success = process_manager.force_kill()
    else:
        success = process_manager.stop()

    if success:
        logger.info("Server stopped successfully.")
        return 0
    else:
        logger.warning("Server was not running or could not be stopped.")
        return 0  # 即使服务未运行，也算作成功停止


@click.command()
@click.option('--force', is_flag=True, help='Force stop')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def stop(force: bool, verbose: bool):
    """Stop the running osins-llama server instance."""
    # 设置日志级别
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    if verbose:
        logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # 仅当logger尚未配置handler时添加，避免重复日志
    if not logger.handlers:
        logger.addHandler(handler)
    # 防止向上级传播日志
    logger.propagate = False

    try:
        # Execute stop command
        result = execute_stop(force=force)
        sys.exit(result)  # 根据执行结果返回相应退出码
    except SystemExit as e:
        sys.exit(e.code)
    except Exception:
        sys.exit(1)  # 发生未预期异常时返回1