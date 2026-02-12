# ConfigManager类实现

## 概述

ConfigManager类负责管理CLI的配置加载、验证和合并，支持从配置文件、环境变量和命令行参数中加载配置。

## 实现要求

1. 实现配置加载功能（从YAML文件、环境变量、命令行参数）
2. 实现配置验证功能（使用Pydantic模型）
3. 实现配置合并功能（按优先级合并不同来源的配置）
4. 提供安全的配置表示（隐藏敏感信息）
5. 防止配置注入攻击

## 代码实现

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

- [ ] 配置加载功能实现完整
- [ ] 配置验证功能实现完整
- [ ] 配置合并功能实现完整
- [ ] 安全配置表示实现
- [ ] 防止配置注入攻击
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 安全加载YAML文件
- 验证配置文件权限
- 隐藏敏感信息
- 防止配置注入

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12