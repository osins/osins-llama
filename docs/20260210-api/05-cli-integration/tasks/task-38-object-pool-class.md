# ObjectPool类实现

## 概述

ObjectPool类用于管理对象池，复用对象以减少创建和销毁的开销。

## 实现要求

1. 实现对象池管理功能
2. 支持对象的获取和释放
3. 限制池的大小
4. 提供超时机制
5. 确保线程安全

## 代码实现

```python
import threading
from queue import Queue, Empty
from typing import TypeVar, Generic
import time


T = TypeVar('T')


class ObjectPool(Generic[T]):
    def __init__(self, create_func, reset_func=None, max_size=10, timeout=30):
        self.create_func = create_func
        self.reset_func = reset_func
        self.max_size = max_size
        self.timeout = timeout
        self.pool = Queue(maxsize=max_size)
        self.lock = threading.Lock()
        self.created_count = 0

    def acquire(self) -> T:
        """获取对象，支持超时等待"""
        try:
            # 尝试立即获取
            obj = self.pool.get_nowait()
        except Empty:
            with self.lock:
                if self.created_count < self.max_size:
                    # 创建新对象
                    obj = self.create_func()
                    self.created_count += 1
                else:
                    # 等待可用对象
                    try:
                        obj = self.pool.get(timeout=self.timeout)
                    except Empty:
                        raise TimeoutError("Could not acquire object from pool within timeout")

        return obj

    def release(self, obj: T):
        """释放对象"""
        if self.reset_func:
            try:
                self.reset_func(obj)
            except Exception as e:
                # 重置失败的对象不应放回池中
                return

        try:
            self.pool.put_nowait(obj)
        except:
            # 池已满，丢弃对象
            pass
```

## 验证标准

- [ ] 对象池管理功能实现完整
- [ ] 对象获取和释放支持
- [ ] 池大小限制
- [ ] 超时机制实现
- [ ] 线程安全实现
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 确保线程安全
- 防止池溢出
- 验证对象安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12