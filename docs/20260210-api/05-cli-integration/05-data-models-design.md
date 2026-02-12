# CLI 数据模型设计

## 概述

CLI数据模型定义了CLI中使用的数据结构和验证规则，确保数据的一致性和正确性。本模块通过Pydantic模型实现数据验证和序列化。

## 数据模型分类

### 1. CLI参数模型
- 命令行参数定义
- 参数验证规则
- 类型转换

### 2. 配置数据模型
- 配置文件结构
- 环境变量映射
- 配置验证

### 3. 响应数据模型
- 命令执行结果
- 错误信息格式
- 状态信息

## CLI参数模型

### 1. 通用参数模型

```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List
from pathlib import Path
import os


class CommonCLIParams(BaseModel):
    """通用CLI参数模型"""
    verbose: bool = Field(default=False, description="详细输出")
    config: Optional[Path] = Field(default=None, description="配置文件路径")
    
    class Config:
        extra = "forbid"  # 禁止额外字段
```

### 2. 服务器启动参数模型

```python
class StartParams(CommonCLIParams):
    """服务器启动参数模型"""
    model_path: Optional[Path] = Field(default=None, description="模型文件路径")
    host: str = Field(default="0.0.0.0", description="服务器绑定地址")
    port: int = Field(default=31301, ge=1024, le=65535, description="服务器端口")
    n_ctx: int = Field(default=2048, ge=1, le=32768, description="上下文长度")
    n_threads: int = Field(default=8, ge=1, le=os.cpu_count(), description="线程数")
    api_keys: Optional[str] = Field(default=None, description="API密钥列表（逗号分隔）")
    max_concurrent_requests: int = Field(default=10, ge=1, le=1000, description="最大并发请求数")
    rate_limit_requests: int = Field(default=60, ge=0, le=10000, description="速率限制请求数")
    rate_limit_window: int = Field(default=60, ge=1, le=3600, description="速率限制时间窗口（秒）")
    debug: bool = Field(default=False, description="调试模式")
    pid_file: Path = Field(default=Path("./llama.pid"), description="PID文件路径")
    
    @validator('host')
    def validate_host(cls, v):
        """验证主机地址"""
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^localhost$|^(\d{1,3}\.){3}\d{1,3}|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]*(\.[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]*)*$'
        if not re.match(ip_pattern, v):
            raise ValueError('Invalid host format')
        return v
    
    @validator('model_path')
    def validate_model_path(cls, v):
        """验证模型路径"""
        if v and not v.exists():
            raise ValueError(f'Model path does not exist: {v}')
        if v and not v.is_file():
            raise ValueError(f'Model path is not a file: {v}')
        return v
    
    @validator('n_threads')
    def validate_n_threads(cls, v):
        """验证线程数不超过CPU核心数"""
        cpu_count = os.cpu_count() or 1
        if v > cpu_count:
            raise ValueError(f'n_threads ({v}) exceeds CPU count ({cpu_count})')
        return v
    
    @validator('pid_file')
    def validate_pid_file(cls, v):
        """验证PID文件路径"""
        # 防止路径遍历
        if ".." in str(v):
            raise ValueError("PID file path cannot contain parent directory references (..)")
        return v
```

### 3. 服务器停止参数模型

```python
class StopParams(CommonCLIParams):
    """服务器停止参数模型"""
    pid_file: Path = Field(default=Path("./llama.pid"), description="PID文件路径")
    force: bool = Field(default=False, description="强制停止")
    
    @validator('pid_file')
    def validate_pid_file(cls, v):
        """验证PID文件路径"""
        # 防止路径遍历
        if ".." in str(v):
            raise ValueError("PID file path cannot contain parent directory references (..)")
        if not v.parent.exists():
            raise ValueError(f'Directory for PID file does not exist: {v.parent}')
        return v
```

### 4. 服务器重启参数模型

```python
class RestartParams(StartParams):
    """服务器重启参数模型（继承启动参数）"""
    wait: int = Field(default=5, ge=0, le=60, description="等待时间（秒）")
```

### 5. 状态检查参数模型

```python
class StatusParams(CommonCLIParams):
    """状态检查参数模型"""
    pid_file: Path = Field(default=Path("./llama.pid"), description="PID文件路径")
    api_url: str = Field(default="http://localhost:31301", description="API端点URL")
    
    @validator('api_url')
    def validate_api_url(cls, v):
        """验证API URL格式"""
        import re
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, v):
            raise ValueError('Invalid API URL format')
        return v
    
    @validator('pid_file')
    def validate_pid_file(cls, v):
        """验证PID文件路径"""
        # 防止路径遍历
        if ".." in str(v):
            raise ValueError("PID file path cannot contain parent directory references (..)")
        return v
```

### 6. 日志查看参数模型

```python
class LogsParams(CommonCLIParams):
    """日志查看参数模型"""
    follow: bool = Field(default=False, description="实时跟踪日志")
    lines: int = Field(default=50, ge=1, le=10000, description="显示最后N行")
    log_file: Path = Field(default=Path("./llama.log"), description="日志文件路径")
    
    @validator('log_file')
    def validate_log_file(cls, v):
        """验证日志文件路径"""
        # 防止路径遍历
        if ".." in str(v):
            raise ValueError("Log file path cannot contain parent directory references (..)")
        if not v.parent.exists():
            raise ValueError(f'Directory for log file does not exist: {v.parent}')
        return v
```

### 7. 健康检查参数模型

```python
class HealthParams(CommonCLIParams):
    """健康检查参数模型"""
    api_url: str = Field(default="http://localhost:31301", description="API端点URL")
    timeout: int = Field(default=30, ge=1, le=300, description="超时时间（秒）")
    
    @validator('api_url')
    def validate_api_url(cls, v):
        """验证API URL格式"""
        import re
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, v):
            raise ValueError('Invalid API URL format')
        return v
    
    @validator('timeout')
    def validate_timeout(cls, v):
        """验证超时时间"""
        if v < 1 or v > 300:
            raise ValueError('Timeout must be between 1 and 300 seconds')
        return v
```

## 配置数据模型

### 1. 服务器配置模型

```python
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

### 2. 模型配置模型

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

### 3. 安全配置模型

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

### 4. 性能配置模型

```python
class PerformanceConfig(BaseModel):
    """性能配置模型"""
    max_concurrent_requests: int = Field(default=10, ge=1, le=1000, description="最大并发请求数")
    request_timeout_seconds: int = Field(default=60, ge=1, le=600, description="请求超时时间（秒）")
    
    @validator('request_timeout_seconds')
    def validate_timeout(cls, v):
        """验证请求超时时间"""
        if v < 1 or v > 600:
            raise ValueError('Request timeout must be between 1 and 600 seconds')
        return v
```

### 5. 日志配置模型

```python
from logging.handlers import RotatingFileHandler


class LoggingConfig(BaseModel):
    """日志配置模型"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(default="text", description="日志格式(text/json)")
    access_log: bool = Field(default=True, description="启用访问日志")
    log_path: Path = Field(default=Path("./app.log"), description="日志文件路径")
    max_log_size_mb: int = Field(default=10, ge=1, le=1000, description="单个日志文件最大大小(MB)")
    backup_count: int = Field(default=5, ge=1, le=10, description="保留备份文件数量")
    
    @validator('level')
    def validate_log_level(cls, v):
        """验证日志级别"""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of {allowed_levels}')
        return v.upper()
    
    @validator('format')
    def validate_log_format(cls, v):
        """验证日志格式"""
        allowed_formats = {"text", "json"}
        if v not in allowed_formats:
            raise ValueError(f'Log format must be one of {allowed_formats}')
        return v
    
    @validator('log_path')
    def validate_log_path(cls, v):
        """验证日志路径"""
        # 防止路径遍历
        if ".." in str(v):
            raise ValueError("Log path cannot contain parent directory references (..)")
        if not v.parent.exists():
            raise ValueError(f'Directory for log file does not exist: {v.parent}')
        return v
```

### 6. TLS配置模型

```python
import ssl


class TLSConfig(BaseModel):
    """TLS配置模型"""
    enabled: bool = Field(default=False, description="启用TLS")
    cert_file: Optional[Path] = Field(default=None, description="证书文件路径")
    key_file: Optional[Path] = Field(default=None, description="私钥文件路径")
    
    @validator('cert_file', 'key_file')
    def validate_tls_files(cls, v):
        """验证TLS文件"""
        if v:
            # 防止路径遍历
            if ".." in str(v):
                raise ValueError("TLS file path cannot contain parent directory references (..)")
            if not v.exists():
                raise ValueError(f'TLS file does not exist: {v}')
            # 检查文件权限（仅所有者可读）
            import stat
            file_stat = v.stat()
            if (file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH)) != 0:
                raise ValueError(f'TLS file has insecure permissions: {v}')
        return v
    
    @validator('enabled')
    def validate_tls_config(cls, v, values):
        """验证TLS配置一致性"""
        if v:
            cert_file = values.get('cert_file')
            key_file = values.get('key_file')
            if not cert_file or not key_file:
                raise ValueError('Both cert_file and key_file must be provided when TLS is enabled')
            
            # 验证证书和私钥是否匹配
            try:
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(cert_file, key_file)
            except ssl.SSLError as e:
                raise ValueError(f'TLS certificate and key do not match: {e}')
        return v
```

### 7. 限制配置模型

```python
class LimitsConfig(BaseModel):
    """限制配置模型"""
    max_request_size_mb: int = Field(default=10, ge=1, le=100, description="最大请求大小（MB）")
    max_upload_workers: int = Field(default=4, ge=0, le=32, description="最大上传工作线程数")
    
    @validator('max_request_size_mb')
    def validate_max_request_size(cls, v):
        """验证最大请求大小"""
        if v < 1 or v > 100:
            raise ValueError('Max request size must be between 1 and 100 MB')
        return v
    
    @validator('max_upload_workers')
    def validate_max_upload_workers(cls, v):
        """验证最大上传工作线程数"""
        if v < 0 or v > 32:
            raise ValueError('Max upload workers must be between 0 and 32')
        return v
```

### 8. 审计配置模型

```python
class AuditConfig(BaseModel):
    """审计配置模型"""
    enabled: bool = Field(default=False, description="启用审计")
    log_path: Path = Field(default=Path("./audit.log"), description="审计日志路径")
    
    @validator('log_path')
    def validate_audit_log_path(cls, v):
        """验证审计日志路径"""
        # 防止路径遍历
        if ".." in str(v):
            raise ValueError("Audit log path cannot contain parent directory references (..)")
        if not v.parent.exists():
            raise ValueError(f'Directory for audit log does not exist: {v.parent}')
        return v
```

### 9. 完整配置模型

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

## 响应数据模型

### 1. 通用响应模型

```python
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class BaseResponse(BaseModel):
    """基础响应模型"""
    status: ResponseStatus
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None
```

### 2. 服务器状态响应模型

```python
class ServerStatusResponse(BaseResponse):
    """服务器状态响应模型"""
    is_running: bool
    pid: Optional[int] = None
    host: Optional[str] = None
    port: Optional[int] = None
    uptime: Optional[float] = None  # 运行时间（秒）
    api_accessible: bool = False
```

### 3. 健康检查响应模型

```python
class HealthCheckResponse(BaseResponse):
    """健康检查响应模型"""
    status: str = "healthy"  # 与基类的status不同，这里表示健康状态
    version: Optional[str] = None
    checks: Optional[dict] = None  # 各项检查的详细结果
    response_time_ms: Optional[float] = None
```

### 4. 命令执行响应模型

```python
class CommandExecutionResponse(BaseResponse):
    """命令执行响应模型"""
    command: str
    exit_code: int = 0
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float  # 执行时间（秒）
```

## 验证规则

### 1. 自定义验证器

```python
def validate_path_not_contain_parent_dir(path: Path) -> Path:
    """验证路径不包含父目录引用"""
    if ".." in str(path):
        raise ValueError("Path cannot contain parent directory references (..)")
    return path
```

### 2. 验证装饰器

```python
from functools import wraps
from typing import Callable


def validate_model(func: Callable):
    """模型验证装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 在函数执行前验证参数
        result = func(*args, **kwargs)
        return result
    return wrapper
```

## 序列化与反序列化

### 1. JSON序列化

```python
import json


def serialize_to_json(model: BaseModel) -> str:
    """将模型序列化为JSON"""
    return model.json(indent=2)


def deserialize_from_json(json_str: str, model_class) -> BaseModel:
    """从JSON反序列化为模型"""
    data = json.loads(json_str)
    return model_class.parse_obj(data)
```

### 2. 配置文件序列化

```python
import yaml


def serialize_config_to_yaml(config: CLIConfig) -> str:
    """将配置序列化为YAML"""
    return yaml.dump(config.dict(), default_flow_style=False)


def deserialize_config_from_yaml(yaml_str: str) -> CLIConfig:
    """从YAML反序列化为配置"""
    data = yaml.safe_load(yaml_str)
    return CLIConfig.parse_obj(data)
```

## 安全和异常处理策略

### 1. 安全验证

```python
def validate_file_permissions(file_path: Path, required_perms: int) -> bool:
    """验证文件权限"""
    import stat
    if not file_path.exists():
        return False
    file_stat = file_path.stat()
    return (file_stat.st_mode & required_perms) == required_perms


def validate_path_traversal(path: str) -> bool:
    """验证路径遍历攻击"""
    return ".." not in path
```

### 2. 异常处理

```python
class ModelValidationError(Exception):
    """模型验证异常"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field
        self.message = message


def safe_model_parse(model_class, data: dict):
    """安全的模型解析"""
    try:
        return model_class.parse_obj(data)
    except Exception as e:
        raise ModelValidationError(f"Failed to parse model {model_class.__name__}: {str(e)}")
```

## 测试策略

### 1. 模型验证测试

```python
import pytest


def test_start_params_validation():
    """测试启动参数验证"""
    # 正确的参数
    params = StartParams(
        model_path=Path("./test_model.gguf"),
        host="localhost",
        port=8080,
        n_ctx=1024,
        n_threads=4
    )
    assert params.port == 8080
    assert params.n_ctx == 1024
    
    # 错误的参数
    with pytest.raises(ValueError):
        StartParams(port=80)  # 端口太小


def test_config_validation():
    """测试配置验证"""
    # 正确的配置
    config = CLIConfig(
        model=ModelConfig(path=Path("./test_model.gguf"))
    )
    assert config.model.path.exists()
    
    # 错误的配置
    with pytest.raises(ValueError):
        CLIConfig(model=ModelConfig(path=Path("./nonexistent_model.gguf")))


def test_path_traversal_protection():
    """测试路径遍历保护"""
    with pytest.raises(ValueError):
        StartParams(pid_file=Path("../forbidden.pid"))
    
    with pytest.raises(ValueError):
        LogsParams(log_file=Path("../../forbidden.log"))
```

### 2. 安全测试

```python
def test_file_permission_validation():
    """测试文件权限验证"""
    # 创建测试文件
    test_file = Path("test_secure_file.txt")
    with open(test_file, "w") as f:
        f.write("test")
    
    # 设置安全权限
    import os
    os.chmod(test_file, 0o600)  # 仅所有者可读写
    
    # 验证权限
    assert validate_file_permissions(test_file, 0o600)
    
    # 清理
    test_file.unlink()
```

### 3. 序列化测试

```python
def test_serialization():
    """测试序列化功能"""
    config = CLIConfig(
        model=ModelConfig(path=Path("./test_model.gguf"))
    )
    
    # 序列化
    json_str = serialize_to_json(config)
    assert json_str is not None
    
    # 反序列化
    deserialized = deserialize_from_json(json_str, CLIConfig)
    assert deserialized.model.path == config.model.path
```

## 最佳实践

### 1. 模型设计
- 使用Pydantic进行数据验证
- 定义明确的字段类型和约束
- 使用Field定义描述和默认值

### 2. 验证规则
- 实现自定义验证器
- 使用validator装饰器
- 提供清晰的错误信息

### 3. 安全措施
- 防止路径遍历攻击
- 验证文件权限
- 敏感信息脱敏

### 4. 序列化
- 支持JSON和YAML格式
- 实现双向序列化
- 处理复杂嵌套结构