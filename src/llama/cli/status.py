"""Status command for osins-llama server."""
import click
import requests  # type: ignore
import logging
import socket
from pathlib import Path

from .pid_file_manager import PidFileManager


def execute_status(debug: bool = False) -> int:
    """
    检查 osins-llama 服务器状态

    Args:
        debug: 是否输出调试日志

    Returns:
        int: 标准退出码
            0: 服务正常运行
            1: PID 文件不存在（服务未运行）
            2: PID 文件存在但端口未被占用
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
            if not pid_data or not pid_data.port:
                logger.info("Service does not exist")
                return 1
            
            port = pid_data.port
            host = pid_data.host or 'localhost'
        except Exception as e:
            logger.info(f"Service does not exist: {e}")
            return 1

        # 检查端口是否被占用
        def is_port_open(host: str, port: int) -> bool:
            """检查指定主机和端口是否开放"""
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)  # 设置3秒超时
                result = sock.connect_ex((host, port))
                sock.close()
                return result == 0
            except Exception:
                return False

        if not is_port_open(host, port):
            logger.warning(f"Port {port} is not occupied, service is not running")
            return 2
        
        logger.info(f"Port {port} is occupied")

        # 检查 API 健康
        try:
            api_url = f"http://{host}:{port}"
            response = requests.get(f"{api_url}/health", timeout=5)
            
            # 直接输出健康检查响应内容
            print(response.text)
            
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
@click.option('--debug/--no-debug', default=False, help='Debug mode')
def status(debug: bool) -> None:
    """Check the server running status."""
    # Execute status command
    result_code = execute_status(debug=debug)

    # Exit with appropriate code
    raise SystemExit(result_code)
