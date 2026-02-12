# ThreadSafeLogger类实现

## 概述

ThreadSafeLogger类用于提供线程安全的日志记录功能，确保多个线程同时记录日志时不会出现问题。

## 实现要求

1. 实现线程安全的日志记录功能
2. 支持多种日志级别
3. 使用锁机制确保线程安全
4. 支持日志轮转

## 代码实现

```python
import threading
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


class ThreadSafeLogger:
    def __init__(self, name: str, log_file: Path, level: str = "INFO", max_bytes: int = 10*1024*1024, backup_count: int = 5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # 防止重复添加handler
        if not self.logger.handlers:
            # 使用旋转日志处理器
            handler = RotatingFileHandler(
                str(log_file),
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.lock = threading.Lock()

    def log(self, level: str, message: str, **kwargs):
        """线程安全地记录日志"""
        with self.lock:
            log_method = getattr(self.logger, level.lower())
            if kwargs:
                log_method(message, extra=kwargs)
            else:
                log_method(message)
```

## 验证标准

- [ ] 线程安全日志记录功能实现完整
- [ ] 多种日志级别支持
- [ ] 锁机制实现
- [ ] 日志轮转支持
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 确保线程安全
- 防止日志文件被篡改
- 验证日志文件权限

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12