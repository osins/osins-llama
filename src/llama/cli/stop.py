"""Stop command for osins-llama server."""
import click
import signal
import os
import sys
import time
import psutil
from .pid_file_manager import PidFileManager
from .process import ProcessManager
from src.llama.utils.pid_tools import find_pid_by_port, is_process_running
from src.llama.core.logger_manager import LoggerManager


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
    # logger_instance.debug(f"Attempting to stop process, force={force}")

    # 使用 ProcessManager 来停止进程
    process_manager = ProcessManager(expected_cmd_keyword="llama.api.server")
    
    if force:
        success = process_manager.force_kill()
    else:
        success = process_manager.stop()

    # 如果通过PID文件方式未能停止，尝试通过端口查找并杀死进程
    if not success:
        logger_instance.info("PID file method failed, trying to kill by port...")

        # 尝试通过端口找到并杀死进程
        try:
            # 默认端口是31301，也可以从PID文件读取
            pid_data = process_manager.pid_manager.read(validate=False)
            port = 31301  # 默认端口
            if pid_data and pid_data.port:
                port = pid_data.port

            logger_instance.info(f"Looking for process on port {port}")
            pid = find_pid_by_port(port)

            if pid:
                logger_instance.info(f"Found process with PID {pid} on port {port}")

                if sys.platform == 'win32':
                    # Windows上使用taskkill命令
                    import subprocess
                    result = subprocess.run(['taskkill', '/PID', str(pid), '/F'],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        logger_instance.info(f"Successfully killed process {pid} on port {port}")
                        success = True
                    else:
                        logger_instance.warning(f"Failed to kill process {pid}: {result.stderr}")
                else:
                    # Unix-like系统上使用kill命令
                    try:
                        if force:
                            os.kill(pid, signal.SIGKILL)
                        else:
                            os.kill(pid, signal.SIGTERM)

                        # 等待进程结束
                        for _ in range(10):  # 等待最多10秒
                            if not is_process_running(pid):
                                logger_instance.info(f"Successfully killed process {pid} on port {port}")
                                success = True
                                break
                            time.sleep(0.5)
                    except ProcessLookupError:
                        logger_instance.info(f"Process {pid} already terminated")
                        success = True
                    except (OSError, PermissionError) as e:
                        logger_instance.warning(f"Permission error killing process {pid}: {e}")
            else:
                logger_instance.info(f"No process found on port {port}")

        except Exception as e:
            logger_instance.error(f"Error during port-based process termination: {e}")

    if success:
        logger_instance.info("Server stopped successfully.")
        return 0
    else:
        logger_instance.warning("Server was not running or could not be stopped.")
        return 0  # 即使服务未运行，也算作成功停止


@click.command()
@click.option('--force', is_flag=True, help='Force stop')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def stop(force: bool, verbose: bool):
    """Stop the running osins-llama server instance."""
    # 如果verbose标志为真，启用调试模式
    if verbose:
        # 设置logger的调试模式
        from src.llama.core.logger_manager import LoggerManager
        global logger
        logger = LoggerManager(debug=True)
    else:
        # 导入默认的logger实例
        from src.llama.core.logger_manager import logger as default_logger
        logger = default_logger

    try:
        # Execute stop command
        result = execute_stop(force=force)
        sys.exit(result)  # 根据执行结果返回相应退出码
    except SystemExit as e:
        sys.exit(e.code)
    except Exception:
        sys.exit(1)  # 发生未预期异常时返回1