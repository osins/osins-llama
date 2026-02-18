"""
logger_manager.py
全局日志管理器封装
"""

import logging
import sys
from typing import Optional

class LoggerManager:
    """
    全局日志封装
    - 统一调用原生 logging API
    - 支持调试模式
    - 可记录请求体/响应体（仅调试）
    - 可在项目中任何位置调用
    """
    _instance = None

    def __new__(cls, name: str = "app_logger", debug: bool = False, log_to_console: bool = True):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger(name, debug, log_to_console)
        return cls._instance

    def _init_logger(self, name: str, debug: bool, log_to_console: bool):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        self._debug_enabled = debug

        # 防止重复添加 handler
        if not self.logger.handlers and log_to_console:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    # --- 封装原生日志方法 ---
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        self.logger.exception(msg, *args, **kwargs)

    # --- 辅助方法 ---
    def log_request(
        self,
        method: str,
        url: str,
        client: Optional[str] = None,
        body: Optional[bytes] = None,
        max_body_log_size: int = 1024
    ):
        """
        用于记录请求信息（仅调试模式）
        """
        if not self._debug_enabled:
            return
        client_info = client or "unknown"
        body_text = "<skipped>"
        if body:
            log_body = body[:max_body_log_size]
            try:
                body_text = log_body.decode("utf-8")
            except Exception:
                body_text = "<cannot decode body>"
        self.logger.debug(f"Request {method} {url} from {client_info} body={body_text}")

    def log_response(
        self,
        method: str,
        url: str,
        client: Optional[str],
        status_code: int,
        process_time: float,
        body: Optional[bytes] = None,
        max_body_log_size: int = 1024
    ):
        """
        用于记录响应信息（仅调试模式）
        """
        if not self._debug_enabled:
            return
        client_info = client or "unknown"
        body_text = "<skipped>"
        if body:
            log_body = body[:max_body_log_size]
            try:
                body_text = log_body.decode("utf-8")
            except Exception:
                body_text = "<cannot decode body>"
        self.logger.debug(
            f"{method} {url} from {client_info} completed in {process_time:.3f}s "
            f"status={status_code} response_body={body_text}"
        )

# 全局实例
logger = LoggerManager(debug=True)


"""
使用示例：

基本使用：
from logger_manager import logger

logger.info("服务启动完成")
logger.debug("调试信息，可包含变量: x=%s", 42)
logger.error("出现错误")
try:
    1 / 0
except Exception as e:
    logger.exception("捕获异常")

请求/响应日志调用（调试用）：
import time

start_time = time.time()
# 模拟请求
method = "POST"
url = "/v1/completions"
client_ip = "127.0.0.1"
request_body = b'{"prompt": "Hello"}'

logger.log_request(method, url, client_ip, request_body)
# ...业务逻辑处理...
process_time = time.time() - start_time
response_body = b'{"result": "World"}'
logger.log_response(method, url, client_ip, 200, process_time, response_body)
"""