"""Status command for osins-llama server."""
import click
import requests  # type: ignore
import logging
from pathlib import Path

from .process import ProcessManager
from .pid_file_manager import PidFileManager


def execute_status(pid_file: Path, api_url: str, debug: bool = False) -> int:
    """
    检查 osins-llama 服务器状态

    Args:
        pid_file: PID 文件路径
        api_url: API 地址
        debug: 是否输出调试日志

    Returns:
        int: 标准退出码
            0: 服务正常运行
            1: PID 文件不存在（服务未运行）
            2: PID 文件存在但进程不存在
            3: API 不可达或返回异常
            4: PID 文件内容非法
            5: 其他异常
    """
    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("status")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    try:
        # 使用 PidFileManager 读取 PID 数据
        pid_manager = PidFileManager()
        try:
            pid_data = pid_manager.read(validate=True)
            if not pid_data or not pid_data.pid:
                logger.info("Service does not exist")
                return 1
            pid = pid_data.pid
        except Exception:
            logger.info("Service does not exist")
            return 1

        process_manager = ProcessManager(
            expected_cmd_keyword="llama.server",
            stop_timeout=30
        )

        # Check if process is running
        is_running = process_manager.is_running()

        if not is_running:
            logger.warning(f"PID file exists but process {pid} not running, cleaning up PID file")
            pid_manager.delete()  # 清理无效的 PID 文件
            return 2
        logger.info(f"Process {pid} is running")

        # 检查 API 健康
        try:
            response = requests.get(f"{api_url}/health", timeout=3)
            if response.status_code == 200:
                logger.info(f"API reachable at {api_url}")
                return 0
            else:
                logger.warning(f"API returned status code {response.status_code}")
                return 3
        except requests.RequestException as e:
            logger.error(f"API check failed: {e}")
            return 3

    except Exception as e:
        logger.exception(f"Unexpected error during status check: {e}")
        return 5


@click.command()
@click.option(
    '--pid-file', default='./llama.pid', type=click.Path(),
    help='PID file path'
)
@click.option('--api-url', default='http://localhost:31301', help='API endpoint URL')
@click.option('--debug/--no-debug', default=False, help='Debug mode')
def status(pid_file: str, api_url: str, debug: bool) -> None:
    """Check the server running status."""
    # Convert string path to Path object
    pid_file_obj = Path(pid_file)

    # Execute status command
    result_code = execute_status(
        pid_file=pid_file_obj,
        api_url=api_url,
        debug=debug
    )

    # Exit with appropriate code
    raise SystemExit(result_code)
