import os
import hmac
from fastapi import HTTPException, Depends, Request
from functools import wraps
import time
import hashlib
import redis
from typing import Optional
from src.llama.config.config import Config
from .rate_limiter import get_rate_limiter


def verify_api_key(request: Request = None, authorization: str = None) -> Optional[str]:
    """
    验证API密钥
    使用 hmac.compare_digest 进行安全的字符串比较，防止时序攻击
    """
    config = Config.from_env()

    if (config.security.api_keys is None or len(config.security.api_keys) == 0) is True:
        DEFAULT_API_KEY = os.getenv("LLAMA_API_KEY", "sk-1234567890abcdef")
        API_KEYS = set([DEFAULT_API_KEY]) if DEFAULT_API_KEY else set()
    else:
        API_KEYS = set(config.security.api_keys)

    if (request is not None and "authorization" in request.headers) is True:
        auth_header = request.headers["authorization"]
    elif authorization is not None:
        auth_header = authorization
    else:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    elif auth_header.startswith("Basic "):
        token = auth_header[6:]
    else:
        token = auth_header

    # 使用 hmac.compare_digest 进行安全的字符串比较
    for api_key in API_KEYS:
        if hmac.compare_digest(token, api_key):
            return token

    raise HTTPException(status_code=401, detail="Invalid API key")


class ConcurrencyController:
    """
    并发控制器
    使用信号量限制同时处理的请求数量
    """
    def __init__(self, config: Config):
        self.config = config
        import asyncio
        self.semaphore = asyncio.Semaphore(config.security.max_concurrent_requests)
        self.active_requests = 0
        self.active_requests_lock = asyncio.Lock()

    async def acquire(self):
        """
        获取并发许可
        """
        await self.semaphore.acquire()
        async with self.active_requests_lock:
            self.active_requests += 1

    async def release(self):
        """
        释放并发许可
        """
        async with self.active_requests_lock:
            self.active_requests -= 1
        self.semaphore.release()

    async def get_status(self):
        """
        获取并发控制器状态
        """
        async with self.active_requests_lock:
            active = self.active_requests
        return {
            "active_requests": active,
            "max_concurrent": self.config.security.max_concurrent_requests,
            "available_permits": self.config.security.max_concurrent_requests - active
        }


def get_concurrency_controller():
    """
    获取并发控制器
    """
    config = Config.from_env()
    return ConcurrencyController(config)