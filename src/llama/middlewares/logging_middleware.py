"""日志中间件，负责记录请求和响应信息"""

import time
import uuid
import hashlib
from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import json
from src.llama.core.logger_manager import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志中间件，记录API请求的详细信息
    包括请求ID、响应时间、请求参数、响应状态等
    注意：不记录敏感信息如prompt原文
    """

    def __init__(self, app):
        """
        初始化日志中间件

        Args:
            app: FastAPI应用实例
        """
        super().__init__(app)
        self.logger = logger

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

        # 对于调试，特别关注 completion 和 chat 路由的请求体
        if request.url.path in ["/v1/completions", "/completion", "/v1/chat/completions"]:
            # 读取请求体用于调试，但要确保它可以被后续处理程序再次读取
            body = await request.body()
            if body:
                try:
                    body_json = json.loads(body.decode('utf-8'))
                    # 仅记录非敏感字段，如模型名称和提示长度
                    model_name = body_json.get('model', 'unknown')
                    prompt_info = 'provided' if 'prompt' in body_json or 'messages' in body_json else 'not provided'
                    prompt_length = 0
                    if 'prompt' in body_json:
                        prompt_val = body_json['prompt']
                        if isinstance(prompt_val, str):
                            prompt_length = len(prompt_val)
                        elif isinstance(prompt_val, list):
                            prompt_length = len(str(prompt_val))
                    elif 'messages' in body_json:
                        messages = body_json['messages']
                        if isinstance(messages, list):
                            prompt_length = sum(len(str(msg)) for msg in messages)
                    
                    self.logger.info(
                        f"DEBUG_REQUEST_BODY - ID: {request_id} | "
                        f"Model: {model_name} | "
                        f"Prompt Info: {prompt_info} | "
                        f"Prompt Length: {prompt_length} | "
                        f"Body Keys: {list(body_json.keys()) if isinstance(body_json, dict) else 'Not a dict'}"
                    )
                except json.JSONDecodeError:
                    self.logger.warning(f"DEBUG_REQUEST_BODY - Could not parse JSON body for request {request_id}")
                
                # 重要：重新包装 request，使 body 可以被后续处理再次读取
                async def receive():
                    return {"type": "http.request", "body": body, "more_body": False}
                
                request._receive = receive  # 替换内部 receive 函数

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
    # 使用全局logger实例
    pass  # logger_manager已经初始化过了，不需要额外配置