
# 任务06：security.rate_limit_function函数

## 任务概述

- **任务编号**: 6
- **任务名称**: 实现速率限制功能
- **文件路径**: `src/llama/utils/rate_limiter.py`
- **函数名称**: `rate_limit_middleware` 和 `check_rate_limit`
- **任务状态**: 待开发
- **优先级**: 中

## 任务描述

实现速率限制功能，控制每个 API Key 的请求频率，包括每秒请求数 (RPS) 和每分钟请求数 (RPM) 限制，防止 API 被滥用。

## 技术要求

- 使用滑动窗口或令牌桶算法实现限流
- 支持 RPS（每秒请求数）和 RPM（每分钟请求数）两种限制方式
- 在分布式环境下可使用 Redis 等外部存储实现限流状态
- 超限返回 HTTP 429 状态码
- 与 API Key 验证功能集成
- 遵循配置文件中的限制参数

## 实现规范

- **输入**: 请求对象、API Key
- **输出**: 布尔值表示是否超过限制
- 超限时返回 HTTP 429
- 使用滑动窗口算法计算请求频率
- 尊重配置中的 `rate_limit_rps` 和 `rate_limit_rpm` 设置
- 提供内存模式和 Redis 模式，保证单实例和分布式环境均可使用

## 代码实现示例

```python
import time
from collections import deque
from fastapi import HTTPException, Request
from typing import Dict
from src.llama.config.config import Config
import redis

class RateLimiter:
    def __init__(self, config: Config):
        self.config = config
        try:
            self.redis_client = redis.Redis(
                host=config.storage.redis_host,
                port=config.storage.redis_port,
                db=config.storage.redis_db
            )
            self.use_redis = True
        except:
            self.requests: Dict[str, deque] = {}
            self.use_redis = False
    
    def check_rate_limit(self, api_key: str) -> bool:
        if self.use_redis:
            return self._check_rate_limit_redis(api_key)
        else:
            return self._check_rate_limit_memory(api_key)
    
    def _check_rate_limit_redis(self, api_key: str) -> bool:
        current_time = time.time()
        rpm_key = f"rate_limit:rpm:{api_key}"
        rps_key = f"rate_limit:rps:{api_key}"
        
        self.redis_client.zremrangebyscore(rpm_key, 0, current_time - 60)
        if self.redis_client.zcard(rpm_key) >= self.config.security.rate_limit_rpm:
            return False
        
        self.redis_client.zremrangebyscore(rps_key, 0, current_time - 1)
        if self.redis_client.zcard(rps_key) >= self.config.security.rate_limit_rps:
            return False
        
        self.redis_client.zadd(rpm_key, {str(current_time): current_time})
        self.redis_client.zadd(rps_key, {str(current_time): current_time})
        self.redis_client.expire(rpm_key, 120)
        self.redis_client.expire(rps_key, 120)
        
        return True
    
    def _check_rate_limit_memory(self, api_key: str) -> bool:
        current_time = time.time()
        if api_key not in self.requests:
            self.requests[api_key] = deque()
        
        while self.requests[api_key] and current_time - self.requests[api_key][0] > 60:
            self.requests[api_key].popleft()
        
        if len(self.requests[api_key]) >= self.config.security.rate_limit_rpm:
            return False
        
        rps_count = sum(1 for t in self.requests[api_key] if current_time - t <= 1)
        if rps_count >= self.config.security.rate_limit_rps:
            return False
        
        self.requests[api_key].append(current_time)
        return True

# 全局限流器实例
rate_limiter: RateLimiter = None

def init_rate_limiter(config: Config):
    global rate_limiter
    rate_limiter = RateLimiter(config)

async def rate_limit_middleware(request: Request, config: Config):
    if not rate_limiter:
        init_rate_limiter(config)
    
    auth_header = request.headers.get("Authorization")
    identifier = request.client.host
    if auth_header and auth_header.startswith("Bearer "):
        identifier = auth_header[len("Bearer "):].strip()
    
    if not rate_limiter.check_rate_limit(identifier):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Limit: {config.security.rate_limit_rps} RPS, "
                   f"{config.security.rate_limit_rpm} RPM"
        )
    
    return True
````

## 验证标准

- 能够正确限制每秒请求数和每分钟请求数
- 超限时返回 HTTP 429
- 限流状态按 API Key 独立维护
- 与 API Key 验证功能集成
- 遵循配置文件中的 `rate_limit_rps` 和 `rate_limit_rpm` 参数

## 相关文档

- [API开发规范](../../2026021001-development-specification.md)
- [安全审计协议](../../2026021100-financial-grade-zero-trust-model-security-audit-protocol.md)

## 依赖关系

- `src/llama/config/config.py`
- FastAPI 框架
- redis-py 库
- collections.deque

## 备注

- 在分布式环境下使用 Redis 实现限流
- 内存模式适用于单实例部署
- 应定期清理过期的限流记录以节省内存
- 可扩展支持更复杂的限流策略
