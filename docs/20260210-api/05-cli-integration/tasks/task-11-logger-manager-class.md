# LoggerManager类实现

## 概述

LoggerManager类负责配置和管理CLI的日志记录功能，包括控制台和文件日志输出、日志格式化和敏感信息过滤。

## 实现要求

1. 实现日志配置功能（支持控制台和文件输出）
2. 实现日志格式化功能（支持文本和JSON格式）
3. 实现日志轮转功能（按大小或时间）
4. 实现敏感信息过滤功能
5. 确保线程安全的日志记录

## 代码实现

```python
"""Production-grade logger configuration."""
import logging
import json
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any


SENSITIVE_FIELDS = {"api_key", "password", "secret", "token"}


class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


class MaskingFilter(logging.Filter):
    """
    Mask sensitive fields in log message.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()

        for field in SENSITIVE_FIELDS:
            if field in msg:
                msg = msg.replace(field, "******")

        record.msg = msg
        return True


class LoggerManager:
    """
    Production-grade logger configuration.
    """

    def __init__(
        self,
        name: str = "llama",
        level: str = "INFO",
        log_file: Optional[Path] = None,
        json_format: bool = False,
        rotate_size_mb: int = 50,
        backup_count: int = 5,
        timed_rotate: bool = False,
    ):
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.log_file = log_file
        self.json_format = json_format
        self.rotate_size_mb = rotate_size_mb
        self.backup_count = backup_count
        self.timed_rotate = timed_rotate

        self.logger = logging.getLogger(self.name)
        self._configure()

    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------

    def _configure(self) -> None:
        self.logger.setLevel(self.level)
        self.logger.propagate = False

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        formatter = (
            JSONFormatter()
            if self.json_format
            else logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
            )
        )

        masking_filter = MaskingFilter()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(masking_filter)
        self.logger.addHandler(console_handler)

        # File handler
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            if self.timed_rotate:
                file_handler = TimedRotatingFileHandler(
                    filename=str(self.log_file),
                    when="midnight",
                    backupCount=self.backup_count,
                    encoding="utf-8",
                )
            else:
                file_handler = RotatingFileHandler(
                    filename=str(self.log_file),
                    maxBytes=self.rotate_size_mb * 1024 * 1024,
                    backupCount=self.backup_count,
                    encoding="utf-8",
                )

            file_handler.setFormatter(formatter)
            file_handler.addFilter(masking_filter)
            self.logger.addHandler(file_handler)

    # ---------------------------------------------------------
    # Public Access
    # ---------------------------------------------------------

    def get_logger(self) -> logging.Logger:
        return self.logger
```

## 验证标准

- [ ] 日志配置功能实现完整
- [ ] 日志格式化功能实现完整
- [ ] 日志轮转功能实现完整
- [ ] 敏感信息过滤功能实现
- [ ] 线程安全日志记录实现
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 敏感信息过滤
- 日志文件权限设置
- 防止日志注入攻击
- 确保线程安全

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12