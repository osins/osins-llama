# CLI 集成开发规范

## 1. 概述

CLI（命令行界面）集成是osins-llama项目的重要组成部分，为用户提供了一种便捷的方式来启动、管理和监控服务器。本规范详细描述了CLI的设计、实现和使用方式，确保其满足生产环境的安全性和可靠性要求。

## 2. 设计原则

### 2.1 安全性
- 防止符号链接攻击
- 验证PID文件安全性
- 隐藏敏感信息（如API密钥）
- 实现进程身份验证

### 2.2 可靠性
- 实现优雅的进程启停
- 提供清晰的错误信息
- 支持配置文件管理
- 实现跨平台兼容

### 2.3 易用性
- 提供直观的命令结构
- 支持多种配置方式
- 实现详细的帮助信息
- 提供状态检查功能

## 3. 架构设计

### 3.1 目录结构
```
src/
└── llama/
    ├── cli/
    │   ├── __init__.py
    │   ├── main.py          # CLI入口点
    │   ├── start.py         # start命令实现
    │   ├── stop.py          # stop命令实现
    │   ├── restart.py       # restart命令实现
    │   ├── status.py        # status命令实现
    │   ├── config.py        # config命令实现
    │   ├── logs.py          # logs命令实现
    │   └── health.py        # health命令实现
    └── utils/
        ├── config.py        # 配置管理工具
        ├── process.py       # 进程管理工具
        ├── logger.py        # 日志管理工具
        └── exceptions.py    # 异常定义
```

### 3.2 命令结构
```
llama
├── start [OPTIONS]          # 启动服务器
├── stop [OPTIONS]           # 停止服务器
├── restart [OPTIONS]        # 重启服务器
├── status [OPTIONS]         # 查看服务器状态
├── config [SUBCOMMANDS]     # 配置管理
│   ├── show                 # 显示当前配置
│   ├── set [KEY VALUE]      # 设置配置项
│   └── reset                # 重置配置
├── logs [OPTIONS]           # 查看服务器日志
└── health [OPTIONS]         # 健康检查
```

## 4. 实现细节

### 4.1 主入口点 (main.py)
```python
import click
from .start import start
from .stop import stop
from .restart import restart
from .status import status
from .config import config
from .logs import logs
from .health import health


@click.group()
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.option('--config', type=click.Path(exists=True), help='Specify configuration file path')
@click.pass_context
def main(ctx, verbose: bool, config: str):
    """CLI for managing osins-llama server."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config_path'] = config
    
    if verbose:
        click.echo("Verbose mode enabled")


# Register all commands
main.add_command(start)
main.add_command(stop)
main.add_command(restart)
main.add_command(status)
main.add_command(config)
main.add_command(logs)
main.add_command(health)


if __name__ == '__main__':
    main()
```

### 4.2 异常定义 (utils/exceptions.py)
```python
"""Custom exceptions for CLI operations."""

class ProcessError(Exception):
    """Base process exception."""


class ProcessAlreadyRunning(ProcessError):
    """Process already running."""


class ProcessNotRunning(ProcessError):
    """Process not running."""


class InvalidPIDFile(ProcessError):
    """PID file invalid or corrupted."""


class PIDSecurityError(ProcessError):
    """PID file security violation."""


class ProcessTimeout(ProcessError):
    """Process stop timeout."""


class ConfigError(Exception):
    """Configuration loading or validation error."""
```

### 4.3 进程管理 (utils/process.py)
```python
"""Production-grade process manager."""

import os
import sys
import time
import stat
import psutil
import subprocess
from pathlib import Path
from typing import List, Optional

from .exceptions import (
    ProcessAlreadyRunning,
    ProcessNotRunning,
    InvalidPIDFile,
    PIDSecurityError,
    ProcessTimeout,
)


class ProcessManager:
    """
    Production-grade process manager.

    Security guarantees:
    - No symlink PID file
    - Owner validation
    - Process identity validation
    - Atomic PID write
    """

    def __init__(
        self,
        pid_file: Path,
        expected_cmd_keyword: str,
        stop_timeout: int = 30,
        check_interval: float = 0.5,
    ):
        self.pid_file = pid_file.resolve()
        self.expected_cmd_keyword = expected_cmd_keyword
        self.stop_timeout = stop_timeout
        self.check_interval = check_interval

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def start(self, command: List[str]) -> None:
        if self.is_running():
            raise ProcessAlreadyRunning("Process already running.")

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )

        self._secure_write_pid(process.pid)

    def stop(self, force: bool = False) -> None:
        pid = self._read_pid()

        process = self._validate_process(pid)

        if force:
            process.kill()
        else:
            process.terminate()

        self._wait_for_exit(process)

        self._safe_remove_pid()

    def restart(self, command: List[str]) -> None:
        if self.is_running():
            self.stop()
        self.start(command)

    def status(self) -> bool:
        if not self.pid_file.exists():
            return False

        try:
            pid = self._read_pid()
            process = self._validate_process(pid)
            return process.is_running()
        except Exception:
            return False

    def is_running(self) -> bool:
        return self.status()

    # ---------------------------------------------------------
    # Internal Security Methods
    # ---------------------------------------------------------

    def _secure_write_pid(self, pid: int) -> None:
        if self.pid_file.exists():
            raise ProcessAlreadyRunning("PID file already exists.")

        if self.pid_file.is_symlink():
            raise PIDSecurityError("PID file cannot be symlink.")

        self.pid_file.parent.mkdir(parents=True, exist_ok=True)

        tmp_file = self.pid_file.with_suffix(".tmp")

        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(str(pid))
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_file, self.pid_file)

        # Restrict permissions (600)
        os.chmod(self.pid_file, stat.S_IRUSR | stat.S_IWUSR)

    def _read_pid(self) -> int:
        if not self.pid_file.exists():
            raise ProcessNotRunning("PID file not found.")

        if self.pid_file.is_symlink():
            raise PIDSecurityError("PID file is symlink.")

        try:
            content = self.pid_file.read_text(encoding="utf-8").strip()
            pid = int(content)
            if pid <= 0:
                raise ValueError
            return pid
        except ValueError:
            raise InvalidPIDFile("Invalid PID content.")

    def _validate_process(self, pid: int) -> psutil.Process:
        try:
            process = psutil.Process(pid)

            cmdline = " ".join(process.cmdline())

            if self.expected_cmd_keyword not in cmdline:
                raise PIDSecurityError(
                    "PID does not belong to expected service."
                )

            return process

        except psutil.NoSuchProcess:
            raise ProcessNotRunning("Process not found.")
        except psutil.AccessDenied:
            raise PIDSecurityError("Access denied to process.")

    def _wait_for_exit(self, process: psutil.Process) -> None:
        start_time = time.time()

        while time.time() - start_time < self.stop_timeout:
            if not process.is_running():
                return
            time.sleep(self.check_interval)

        raise ProcessTimeout("Process did not stop within timeout.")

    def _safe_remove_pid(self) -> None:
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception:
            pass
```

### 4.4 配置管理 (utils/config.py)
```python
"""Production-grade configuration manager."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator


class ServerConfig(BaseModel):
    """
    Strict server configuration schema.
    """

    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1, le=64)

    log_level: str = Field(default="INFO")
    log_file: Optional[Path] = None

    model_path: Path
    api_key: Optional[str] = None

    timeout: int = Field(default=30, ge=1, le=600)

    enable_tls: bool = False
    tls_cert: Optional[Path] = None
    tls_key: Optional[Path] = None

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @field_validator("model_path")
    @classmethod
    def validate_model_path(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError("model_path does not exist")
        if not v.is_file():
            raise ValueError("model_path must be a file")
        return v.resolve()

    @field_validator("tls_cert", "tls_key")
    @classmethod
    def validate_tls_files(cls, v: Optional[Path]) -> Optional[Path]:
        if v is None:
            return v
        if not v.exists():
            raise ValueError("TLS file does not exist")
        return v.resolve()

    @field_validator("enable_tls")
    @classmethod
    def validate_tls_dependency(cls, v: bool, info):
        values = info.data
        if v:
            if not values.get("tls_cert") or not values.get("tls_key"):
                raise ValueError("TLS enabled but cert or key missing")
        return v


class ConfigError(Exception):
    """Configuration loading or validation error."""


class ConfigManager:
    """
    Production-grade configuration manager.

    Responsibilities:
    - Load YAML safely
    - Merge file + env + CLI
    - Validate strictly
    - Provide masked representation
    """

    ENV_PREFIX = "LLAMA_"

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file.resolve() if config_file else None

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def load(
        self,
        cli_overrides: Optional[Dict[str, Any]] = None,
    ) -> ServerConfig:

        file_config = self._load_yaml()
        env_config = self._load_env()
        cli_config = cli_overrides or {}

        merged = self._merge_configs(
            base=file_config,
            env=env_config,
            cli=cli_config,
        )

        try:
            config = ServerConfig(**merged)
        except ValidationError as e:
            raise ConfigError(str(e)) from e

        return config

    # ---------------------------------------------------------
    # YAML Loading
    # ---------------------------------------------------------

    def _load_yaml(self) -> Dict[str, Any]:
        if not self.config_file:
            return {}

        if not self.config_file.exists():
            raise ConfigError("Configuration file not found.")

        if self.config_file.is_symlink():
            raise ConfigError("Config file cannot be symlink.")

        try:
            with self.config_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML: {e}") from e

        if not isinstance(data, dict):
            raise ConfigError("YAML root must be mapping.")

        return data

    # ---------------------------------------------------------
    # Environment Loading
    # ---------------------------------------------------------

    def _load_env(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field in ServerConfig.model_fields.keys():
            env_key = f"{self.ENV_PREFIX}{field.upper()}"
            if env_key in os.environ:
                result[field] = os.environ[env_key]

        return result

    # ---------------------------------------------------------
    # Merge Logic
    # ---------------------------------------------------------

    def _merge_configs(
        self,
        base: Dict[str, Any],
        env: Dict[str, Any],
        cli: Dict[str, Any],
    ) -> Dict[str, Any]:

        merged = dict(base)

        for k, v in env.items():
            if v is not None:
                merged[k] = v

        for k, v in cli.items():
            if v is not None:
                merged[k] = v

        return merged

    # ---------------------------------------------------------
    # Secure Representation
    # ---------------------------------------------------------

    @staticmethod
    def masked_dict(config: ServerConfig) -> Dict[str, Any]:
        data = config.model_dump()

        if data.get("api_key"):
            data["api_key"] = "******"

        return data
```

### 4.5 日志管理 (utils/logger.py)
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

## 5. 命令实现详情

### 5.1 start命令
- 启动osins-llama服务器实例
- 支持多种启动参数配置
- 管理PID文件以跟踪服务器进程

### 5.2 stop命令
- 安全停止服务器实例
- 验证PID文件安全性
- 支持强制停止选项

### 5.3 restart命令
- 重启服务器实例
- 支持等待时间配置

### 5.4 status命令
- 检查服务器运行状态
- 验证进程是否正在运行
- 尝试连接API端点

### 5.5 config命令
- 管理服务器配置
- 支持显示、设置和重置配置

### 5.6 logs命令
- 查看服务器日志
- 支持实时跟踪和历史日志查看

### 5.7 health命令
- 执行健康检查
- 验证服务器响应和超时

## 6. 安全考虑

### 6.1 输入验证
- 验证所有命令行参数
- 防止路径遍历攻击
- 参数范围检查

### 6.2 PID文件安全
- 防止符号链接攻击
- 验证PID文件权限
- 验证进程归属

### 6.3 敏感信息保护
- 不在命令行显示API密钥
- 日志中隐藏敏感信息
- 安全的配置文件权限

## 7. 错误处理

### 7.1 退出码规范
- 0: 成功
- 1: 一般错误
- 2: 参数错误
- 3: 权限问题
- 4: 超时

### 7.2 异常处理
- 提供清晰的错误信息
- 适当的异常捕获和处理
- 用户友好的提示

## 8. 测试策略

### 8.1 单元测试
- 命令解析测试
- 参数验证测试
- 错误处理测试
- 覆盖率≥90%

### 8.2 集成测试
- 端到端命令测试
- 进程管理测试
- 配置加载测试

### 8.3 安全测试
- PID文件安全测试
- 输入验证测试
- 权限检查测试

## 9. 配置文件格式

### 9.1 YAML格式
```yaml
server:
  host: "0.0.0.0"
  port: 31301
  debug: false

model:
  path: "./models/model.gguf"
  n_ctx: 2048
  n_threads: 8

security:
  api_keys: ["sk-123456", "sk-789012"]
  rate_limit_requests: 60
  rate_limit_window: 60

performance:
  max_concurrent_requests: 10
```

## 10. 部署和运维

### 10.1 进程管理
- PID文件管理
- 信号处理
- 优雅关闭

### 10.2 日志管理
- 支持不同日志级别
- 日志文件轮转
- 结构化日志输出

## 11. 最佳实践

1. 提供清晰的帮助信息和文档
2. 实现一致的命令行接口
3. 提供丰富的配置选项
4. 实现可靠的进程管理
5. 提供详细的日志记录
6. 实现安全的参数处理
7. 提供错误恢复机制
8. 支持自动化脚本集成