# RateLimiter类实现

## 概述

RateLimiter类用于实现CLI命令的速率限制功能，防止请求过于频繁。

## 实现要求

1. 实现请求速率限制功能
2. 支持时间窗口限制
3. 确保线程安全
4. 提供检查请求是否被允许的方法

## 代码实现

```python
import time
from typing import Dict
from collections import defaultdict, deque
import threading


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def is_allowed(self, identifier: str = "default") -> bool:
        """检查请求是否被允许"""
        with self.lock:
            now = time.time()

            # 清理过期的请求记录 - 使用双端队列优化
            while (self.requests[identifier] and
                   now - self.requests[identifier][0] >= self.window_seconds):
                self.requests[identifier].popleft()

            # 检查是否超过限制
            if len(self.requests[identifier]) >= self.max_requests:
                return False

            # 记录当前请求
            self.requests[identifier].append(now)
            return True
```

## 验证标准

- [ ] 速率限制功能实现完整
- [ ] 时间窗口限制支持
- [ ] 线程安全实现
- [ ] 请求检查方法实现
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 确保线程安全
- 防止速率限制绕过
- 验证参数安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12