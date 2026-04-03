"""Stop command for osins-llama server."""
import click
import signal
import os
import sys
import time
import psutil
from .pid_file_manager import PidFileManager
from .process import ProcessManager
from llama.utils.pid_tools import find_pid_by_port, is_process_running
from llama.core.logger_manager import LoggerManager


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
    logger_instance = LoggerManager(debug=False)

    process_manager = ProcessManager(expected_cmd_keyword="llama.api.server")
    
    try:
        if force:
            success = process_manager.force_kill()
        else:
            success = process_manager.stop()
    except ValueError as e:
        logger_instance.error(str(e))
        return 1

    if success:
        logger_instance.info("Server stopped successfully.")
        return 0
    else:
        logger_instance.warning("Server was not running or could not be stopped.")
        return 0


@click.command()
@click.option('--force', is_flag=True, help='Force stop')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def stop(force: bool, verbose: bool):
    """Stop the running osins-llama server instance."""
    # 如果verbose标志为真，启用调试模式
    if verbose:
        # 设置logger的调试模式
        from llama.core.logger_manager import LoggerManager
        global logger
        logger = LoggerManager(debug=True)
    else:
        # 导入默认的logger实例
        from llama.core.logger_manager import logger as default_logger
        logger = default_logger

    try:
        # Execute stop command
        result = execute_stop(force=force)
        sys.exit(result)  # 根据执行结果返回相应退出码
    except SystemExit as e:
        sys.exit(e.code)
    except Exception:
        sys.exit(1)  # 发生未预期异常时返回1