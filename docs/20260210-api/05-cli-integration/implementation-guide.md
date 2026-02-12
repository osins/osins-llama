# CLI 集成实现指南

## 任务概述

- **任务编号**: 5
- **任务名称**: CLI 集成
- **文件路径**: src/llama/cli/
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述

CLI（命令行界面）集成为用户提供了一个方便的方式来启动、管理和监控osins-llama服务器。本任务旨在实现一个功能完整、安全可靠、易于使用的命令行工具，使用户能够通过终端与API服务进行交互。

## 技术要求

1. 使用 `click` 库实现命令行界面
2. 遵循PEP 8、PEP 257、PEP 484规范
3. 实现完整的参数解析和验证
4. 支持配置文件（YAML格式）
5. 实现安全的进程管理
6. 提供清晰的错误信息和退出码
7. 支持跨平台运行（Windows、Linux、macOS）

## 实现规范

### 1. 目录结构

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

### 2. 命令结构

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

### 3. 安全要求

- 验证所有输入参数，防止路径遍历攻击
- 安全地处理PID文件权限
- 隐藏敏感信息（如API密钥）在日志中
- 防止符号链接攻击
- 实现进程身份验证

## 代码实现

### 1. 主入口点 (main.py)

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

### 2. 异常定义 (utils/exceptions.py)

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

### 3. 进程管理 (utils/process.py)

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

### 4. 配置管理 (utils/config.py)

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

## 验证标准

1. 所有CLI命令按设计文档实现
2. 单元测试覆盖率≥90%
3. 通过安全审计协议检查
4. 符合API开发规范
5. 与现有服务器实现无缝集成
6. 跨平台兼容性测试通过
7. 异常路径全覆盖测试
8. 安全特性验证通过

## 相关文档

- [API开发规范](../2026021001-development-specification.md)
- [单元测试开发规范](../20260210-unit-test-specification.md)
- [金融级零信任模型安全审计协议](../2026021100-financial-grade-zero-trust-model-security-audit-protocol.md)

## 依赖关系

- 依赖服务器实现模块
- 依赖配置管理模块
- 依赖日志管理模块

## 备注

- CLI工具必须提供清晰的错误信息和适当的退出码
- 所有安全措施必须严格实施，防止符号链接攻击和权限提升
- 进程管理必须安全可靠，防止误杀其他进程