# 任务07：concurrency_control.async_semaphore_function

## 任务概述

- **任务编号**: 7
- **任务名称**: 实现并发控制功能
- **文件路径**: `src/llama/core/concurrency_controller.py`
- **函数名称**: `ConcurrencyController.acquire_permit`, `ConcurrencyController.release_permit`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述

实现并发控制功能，使用信号量(Semaphore)限制同时处理的请求数量，确保模型实例在高并发情况下的安全推理，并实现请求排队机制。

## 技术要求

- 使用 `asyncio.Semaphore` 控制最大同时请求数（单实例）
- 分布式环境下使用 Redis 协调多实例并发控制
- 队列长度由 `config.resources.max_queue_size` 配置
- 超过队列或请求超时返回 HTTP 429/504
- 严格串行确保单一模型实例安全推理
- 与模型管理器集成
- 实现超时控制机制

## 实现规范

- **输入**: 配置对象
- **输出**: 信号量控制的上下文管理器
- 超过并发限制时请求进入队列
- 队列满时返回 HTTP 429
- 请求超时时返回 HTTP 504
- 遵循配置中的 `max_concurrent_requests` 和 `request_timeout_seconds` 设置

## 代码实现示例

```python
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import HTTPException
from typing import Optional
from src.llama.config.config import Config
import redis

class ConcurrencyController:
    def __init__(self, config: Config):
        self.config = config
        try:
            self.redis_client = redis.Redis(
                host=config.storage.redis_host,
                port=config.storage.redis_port,
                db=config.storage.redis_db,
                password=config.storage.redis_password or None
            )
            self.use_redis = True
            self.concurrent_key = "concurrent_requests"
            self.queue_key = "request_queue"
        except:
            self.semaphore = asyncio.Semaphore(config.resources.max_concurrent_requests)
            self.waiting_queue = asyncio.Queue(maxsize=config.resources.max_queue_size)
            self.active_requests = 0
            self.active_requests_lock = asyncio.Lock()
            self.use_redis = False
    
    @asynccontextmanager
    async def acquire_permit(self):
        if self.use_redis:
            async with self._acquire_permit_redis():
                yield
        else:
            async with self._acquire_permit_local():
                yield
    
    @asynccontextmanager
    async def _acquire_permit_redis(self):
        current_concurrent = int(self.redis_client.get(self.concurrent_key) or 0)
        if current_concurrent >= self.config.resources.max_concurrent_requests:
            queue_size = self.redis_client.llen(self.queue_key)
            if queue_size >= self.config.resources.max_queue_size:
                raise HTTPException(status_code=429, detail="Too many concurrent requests")
            self.redis_client.rpush(self.queue_key, "waiting_request")
        self.redis_client.incr(self.concurrent_key)
        try:
            yield
        finally:
            self.redis_client.decr(self.concurrent_key)
            if self.redis_client.llen(self.queue_key) > 0:
                self.redis_client.lpop(self.queue_key)
    
    @asynccontextmanager
    async def _acquire_permit_local(self):
        if self.waiting_queue.full():
            raise HTTPException(status_code=429, detail="Too many concurrent requests")
        queue_item = asyncio.Event()
        try:
            await self.waiting_queue.put(queue_item)
            try:
                await asyncio.wait_for(
                    self.semaphore.acquire(),
                    timeout=self.config.resources.request_timeout_seconds
                )
            except asyncio.TimeoutError:
                try:
                    self.waiting_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                raise HTTPException(status_code=504, detail="Request timeout")
            async with self.active_requests_lock:
                self.active_requests += 1
            yield
        finally:
            self.semaphore.release()
            async with self.active_requests_lock:
                self.active_requests -= 1
            try:
                await self.waiting_queue.get()
            except asyncio.QueueEmpty:
                pass
    
    async def get_status(self):
        if self.use_redis:
            active = int(self.redis_client.get(self.concurrent_key) or 0)
            queue_size = self.redis_client.llen(self.queue_key)
            return {
                "active_requests": active,
                "max_concurrent": self.config.resources.max_concurrent_requests,
                "queue_size": queue_size,
                "max_queue_size": self.config.resources.max_queue_size
            }
        else:
            async with self.active_requests_lock:
                active = self.active_requests
            return {
                "active_requests": active,
                "max_concurrent": self.config.resources.max_concurrent_requests,
                "queue_size": self.waiting_queue.qsize(),
                "max_queue_size": self.config.resources.max_queue_size
            }

# 全局并发控制器实例
concurrency_controller: Optional[ConcurrencyController] = None

def init_concurrency_controller(config: Config):
    global concurrency_controller
    concurrency_controller = ConcurrencyController(config)
    return concurrency_controller

def get_concurrency_controller() -> ConcurrencyController:
    global concurrency_controller
    if concurrency_controller is None:
        raise RuntimeError("Concurrency controller not initialized")
    return concurrency_controller
````

## 验证标准

- 正确限制并发请求数
- 队列机制正常工作
- 超时控制按配置生效
- 超过队列限制时返回 HTTP 429
- 请求超时时返回 HTTP 504
- 与模型管理器集成
- 并发安全保障有效
- 分布式环境下通过 Redis 协调多实例并发

## 相关文档

- [API开发规范](../../2026021001-development-specification.md)
- [安全审计协议](../../2026021100-financial-grade-zero-trust-model-security-audit-protocol.md)

## 依赖关系

- `src/llama/config/config.py`
- FastAPI
- asyncio
- redis-py

## 备注

- 分布式环境下使用 Redis 协调并发控制
- 提供监控接口以观察并发状态
- 可根据模型负载动态调整并发数
