"""Stop command for osins-llama server."""
import click
import logging
import signal
import os
import sys
import time
from pathlib import Path
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

    # 初始化 ProcessManager
    process_manager = ProcessManager(
        expected_cmd_keyword="llama.api.server",
        stop_timeout=30
    )

    # 获取PID
    pid = process_manager.get_pid()
    if not pid:
        logger.warning("No PID found, process may not be running")
        return 0  # PID不存在，认为服务已停止

    logger.info(f"Stopping process {pid}")

    # 通过 ProcessManager 停止进程
    try:
        if force:
            # 强制停止：直接发送 SIGKILL 信号
            logger.info(f"Force stopping process {pid}")
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                logger.info(f"Process {pid} already terminated")
                # 即使进程已终止，也要清理PID文件
                process_manager.pid_manager.delete()
                return 0
            except (OSError, PermissionError) as e:
                logger.error(f"Failed to send SIGKILL to process {pid}: {e}")
                return 1  # 强制停止失败
        else:
            # 优雅停止：发送 SIGTERM 信号
            os.kill(pid, signal.SIGTERM)

            # 等待进程终止
            max_wait_time = 30  # 最多等待30秒
            wait_interval = 0.5
            elapsed = 0

            while elapsed < max_wait_time:
                try:
                    os.kill(pid, 0)  # 检查进程是否仍在运行
                    time.sleep(wait_interval)
                    elapsed += wait_interval
                except ProcessLookupError:
                    logger.info(f"Process {pid} has been terminated gracefully")
                    break
            else:
                # 超时仍未终止，强制终止
                logger.warning(f"Process {pid} did not terminate gracefully, forcing termination")
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    # 进程在强制终止前已结束
                    logger.info(f"Process {pid} has been terminated after SIGKILL")
                    return 0
                except (OSError, PermissionError) as e:
                    logger.error(f"Failed to send SIGKILL to process {pid}: {e}")
                    return 1  # 强制停止失败

    except ProcessLookupError:
        logger.info(f"Process {pid} has been terminated")
        return 0  # 正常终止
    except PermissionError as e:
        logger.error(f"Permission denied when stopping process {pid}: {e}")
        return 1  # 权限错误
    except OSError as e:
        logger.error(f"OS error when stopping process {pid}: {e}")
        return 1  # 其他系统错误

    return 0  # 成功停止
    


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