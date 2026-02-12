# 配置管理服务

## 概述

配置管理服务负责加载、验证和保存CLI的配置文件，确保系统按预期运行。

## 服务职责

- 加载配置文件
- 验证配置有效性
- 保存配置到文件
- 提供配置访问接口

## 配置模型

### 服务器配置

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from pathlib import Path
import os


class ServerConfig(BaseModel):
    """服务器配置模型"""
    host: str = Field(default="127.0.0.1", description="服务器主机地址")
    port: int = Field(default=8000, ge=1024, le=65535, description="服务器端口")
    debug: bool = Field(default=False, description="调试模式")
    
    @validator('host')
    def validate_host(cls, v):
        """验证主机地址"""
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^localhost$|^(\d{1,3}\.){3}\d{1,3}|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]*(\.[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]*)*$'
        if not re.match(ip_pattern, v):
            raise ValueError('Invalid host format')
        return v
```

### 模型配置

```python
class ModelConfig(BaseModel):
    """模型配置模型"""
    path: Path = Field(description="模型文件路径")
    n_ctx: int = Field(default=2048, ge=1, le=32768, description="上下文长度")
    n_threads: int = Field(default=8, ge=1, le=os.cpu_count(), description="线程数")
    
    @validator('path')
    def validate_model_path(cls, v):
        """验证模型路径"""
        if not v.exists():
            raise ValueError(f'Model path does not exist: {v}')
        if not v.is_file():
            raise ValueError(f'Model path is not a file: {v}')
        if not v.suffix.lower() == '.gguf':
            raise ValueError(f'Model file must have .gguf extension: {v}')
        # 防止路径遍历
        if ".." in str(v):
            raise ValueError("Model path cannot contain parent directory references (..)")
        return v.resolve()  # 返回绝对路径
```

### 安全配置

```python
import stat


class SecurityConfig(BaseModel):
    """安全配置模型"""
    api_keys_file: Optional[Path] = Field(default=None, description="API密钥文件路径")
    rate_limit: Optional[dict] = Field(default=None, description="速率限制配置")
    enable_ip_limit: bool = Field(default=True, description="启用IP限制")
    
    @validator('api_keys_file')
    def validate_api_keys_file(cls, v):
        """验证API密钥文件"""
        if v:
            # 防止路径遍历
            if ".." in str(v):
                raise ValueError("API keys file path cannot contain parent directory references (..)")
            if not v.exists():
                raise ValueError(f'API keys file does not exist: {v}')
            # 检查文件权限（仅所有者可读）
            file_stat = v.stat()
            if (file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH)) != 0:
                raise ValueError(f'API keys file has insecure permissions: {v}')
        return v
```

### 完整配置模型

```python
class CLIConfig(BaseModel):
    """完整CLI配置模型"""
    server: ServerConfig = Field(default_factory=ServerConfig)
    model: ModelConfig
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    tls: TLSConfig = Field(default_factory=TLSConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    
    class Config:
        extra = "forbid"  # 禁止额外字段
```

## 配置服务实现

```python
import yaml
import logging
from pathlib import Path
from typing import Optional


class ConfigService:
    """配置服务"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def load_config(self, config_path: Optional[Path] = None) -> CLIConfig:
        """加载配置"""
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                config = CLIConfig.parse_obj(config_data)
                self.logger.info(f"Configuration loaded from {config_path}")
                return config
            except Exception as e:
                self.logger.error(f"Failed to load configuration from {config_path}: {str(e)}")
                raise
        else:
            # 返回默认配置
            self.logger.info("Using default configuration")
            return CLIConfig(
                model=ModelConfig(path=Path("./models/model.gguf"))
            )
    
    def save_config(self, config: CLIConfig, config_path: Path):
        """保存配置"""
        try:
            config_dir = config_path.parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config.dict(), f, default_flow_style=False)
            
            self.logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {config_path}: {str(e)}")
            raise
    
    def validate_config(self, config: CLIConfig) -> list:
        """验证配置"""
        errors = []
        
        # 验证模型路径
        if not config.model.path.exists():
            errors.append(f"Model path does not exist: {config.model.path}")
        
        # 验证端口范围
        if config.server.port < 1024 or config.server.port > 65535:
            errors.append(f"Port must be between 1024 and 65535, got {config.server.port}")
        
        # 验证上下文长度
        if config.model.n_ctx < 1 or config.model.n_ctx > 32768:
            errors.append(f"Context length must be between 1 and 32768, got {config.model.n_ctx}")
        
        # 验证线程数
        cpu_count = os.cpu_count() or 1
        if config.model.n_threads < 1 or config.model.n_threads > cpu_count:
            errors.append(f"Threads must be between 1 and {cpu_count}, got {config.model.n_threads}")
        
        return errors
```

## 配置验证器

```python
class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_config_fields(config: CLIConfig) -> list:
        """验证配置字段"""
        errors = []
        
        # 检查所有必需字段
        if not config.model.path:
            errors.append("Model path is required")
        
        # 验证路径安全性
        if ".." in str(config.model.path):
            errors.append("Model path contains unsafe path traversal")
        
        return errors
```

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12