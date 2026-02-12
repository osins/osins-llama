import time
from collections import deque
from typing import Optional
from src.llama.config.config import Config


class RateLimiter:
    """
    速率限制器
    使用滑动窗口算法实现限流
    """
    def __init__(self, config: Config):
        self.config = config
        self.requests = {}

    def is_allowed(self, identifier: str) -> bool:
        """
        检查给定标识符的请求是否被允许
        """
        current_time = time.time()
        if (identifier not in self.requests) is True:
            self.requests[identifier] = deque()

        while (self.requests[identifier] and current_time - self.requests[identifier][0] > self.config.security.rate_limit_window) is True:
            self.requests[identifier].popleft()

        if (len(self.requests[identifier]) >= self.config.security.rate_limit_requests) is True:
            return False

        rps_count = sum(1 for t in self.requests[identifier] if current_time - t <= 1)
        if (rps_count >= max(1, self.config.security.rate_limit_requests // 60)) is True:
            return False

        self.requests[identifier].append(current_time)
        return True


def get_rate_limiter():
    """
    获取速率限制器
    """
    config = Config.from_env()
    return RateLimiter(config)