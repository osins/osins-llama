# LRUCache类实现

## 概述

LRUCache类用于实现最近最少使用(LRU)缓存，提高数据访问性能。

## 实现要求

1. 实现LRU缓存功能
2. 支持缓存大小限制
3. 支持TTL(生存时间)机制
4. 确保线程安全
5. 提供缓存命中和未命中的统计

## 代码实现

```python
import threading
import time
from typing import Any, Optional
from collections import OrderedDict


class LRUCache:
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                return None

            # 检查是否过期
            if time.time() - self.timestamps[key] > self.ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None

            # 移动到末尾（最近使用）
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value: Any):
        """设置缓存值"""
        with self.lock:
            if key in self.cache:
                # 更新现有键
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.max_size:
                # 删除最久未使用的项
                oldest_key, _ = self.cache.popitem(last=False)
                del self.timestamps[oldest_key]

            self.cache[key] = value
            self.timestamps[key] = time.time()
```

## 验证标准

- [ ] LRU缓存功能实现完整
- [ ] 缓存大小限制支持
- [ ] TTL机制实现
- [ ] 线程安全实现
- [ ] 缓存统计功能
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 确保线程安全
- 防止缓存污染
- 验证键值安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12