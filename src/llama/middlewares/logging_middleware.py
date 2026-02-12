"""日志中间件，负责记录请求和响应信息"""

import time
import uuid
import hashlib
from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import logging
import json


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志中间件，记录API请求的详细信息
    包括请求ID、响应时间、请求参数、响应状态等
    注意：不记录敏感信息如prompt原文
    """

    def __init__(self, app, logger: logging.Logger = None):
        """
        初始化日志中间件

        Args:
            app: FastAPI应用实例
            logger: 日志记录器实例
        """
        super().__init__(app)
        self.logger = logger or logging.getLogger(__name__)

        # 设置日志格式
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[StarletteResponse]]) -> StarletteResponse:
        """
        处理请求并记录日志

        Args:
            request: 请求对象
            call_next: 调用下一个中间件或路由处理函数

        Returns:
            响应对象
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始时间
        start_time = time.time()

        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"

        # 获取并哈希API密钥（不记录明文）
        api_key_hash = None
        auth_header = request.headers.get("authorization")
        if auth_header:
            # 提取API密钥并进行哈希
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]
            elif auth_header.startswith("Basic "):
                api_key = auth_header[6:]
            else:
                api_key = auth_header
            
            # 对API密钥进行哈希处理，避免记录明文
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]

        # 记录请求信息（不包含敏感内容）
        self.logger.info(
            f"REQUEST_START - ID: {request_id} | "
            f"Method: {request.method} | "
            f"URL: {str(request.url)} | "
            f"ClientIP: {client_ip} | "
            f"APIKeyHash: {api_key_hash} | "
            f"Headers: {self._sanitize_headers(dict(request.headers))}"
        )

        try:
            # 调用下一个中间件或路由处理函数
            response = await call_next(request)

            # 计算响应时间
            process_time = time.time() - start_time

            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            # 记录响应信息
            self.logger.info(
                f"REQUEST_END - ID: {request_id} | "
                f"Status: {response.status_code} | "
                f"ProcessTime: {process_time:.4f}s | "
                f"Content-Length: {response.headers.get('content-length', 'unknown')} | "
                f"ClientIP: {client_ip}"
            )

            return response

        except Exception as e:
            # 记录异常信息
            process_time = time.time() - start_time
            self.logger.error(
                f"REQUEST_ERROR - ID: {request_id} | "
                f"ClientIP: {client_ip} | "
                f"Error: {str(e)} | "
                f"ProcessTime: {process_time:.4f}s",
                exc_info=True  # 记录异常堆栈
            )

            # 重新抛出异常
            raise

    def _sanitize_headers(self, headers: dict) -> dict:
        """
        清理请求头，隐藏敏感信息

        Args:
            headers: 原始请求头字典

        Returns:
            清理后的请求头字典
        """
        sanitized = headers.copy()

        # 隐藏敏感头部信息
        sensitive_headers = ['authorization', 'x-api-key', 'cookie', 'set-cookie']

        for header_name in sensitive_headers:
            if header_name.lower() in sanitized:
                sanitized[header_name.lower()] = "***REDACTED***"

        return sanitized


def setup_logging_config():
    """
    设置日志配置
    """
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )