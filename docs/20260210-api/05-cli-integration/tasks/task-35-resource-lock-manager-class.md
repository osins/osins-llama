# ResourceLockManager类实现

## 概述

ResourceLockManager类用于管理资源锁，防止多个命令同时访问同一资源。

## 实现要求

1. 实现资源锁管理功能
2. 支持多种资源的锁管理
3. 提供上下文管理器接口
4. 确保线程安全

## 代码实现

```python
import threading
from contextlib import contextmanager
from typing import Dict


class ResourceLockManager:
    def __init__(self):
        self.locks: Dict[str, threading.RLock] = {}
        self.global_lock = threading.RLock()  # 使用RLock避免死锁

    @contextmanager
    def lock_resource(self, resource_id: str):
        """获取资源锁的上下文管理器"""
        with self.global_lock:
            if resource_id not in self.locks:
                self.locks[resource_id] = threading.RLock()
            lock = self.locks[resource_id]

        acquired = lock.acquire(timeout=10)  # 10秒超时
        if not acquired:
            raise TimeoutError(f"Could not acquire lock for resource {resource_id}")

        try:
            yield
        finally:
            lock.release()

    def is_locked(self, resource_id: str) -> bool:
        """检查资源是否被锁定（简化实现）"""
        with self.global_lock:
            return resource_id in self.locks and self.locks[resource_id]._is_owned()
```

## 验证标准

- [ ] 资源锁管理功能实现完整
- [ ] 多资源锁支持
- [ ] 上下文管理器接口实现
- [ ] 线程安全实现
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 确保线程安全
- 防止死锁
- 验证资源ID安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12