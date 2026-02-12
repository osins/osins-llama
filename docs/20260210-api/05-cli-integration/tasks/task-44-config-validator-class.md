# ConfigValidator类实现

## 概述

ConfigValidator类负责验证CLI配置参数的有效性，确保系统按预期运行。

## 实现要求

1. 实现配置验证功能
2. 支持启动配置验证
3. 验证服务器可用性
4. 验证配置字段
5. 提供详细的错误信息

## 代码实现

```python
from typing import List
import os


class ConfigValidator:
    """配置验证器"""

    @staticmethod
    def validate_start_config(params) -> List[str]:
        """验证启动配置"""
        errors = []

        # 验证模型路径
        if params.model_path and not params.model_path.exists():
            errors.append(f"Model path does not exist: {params.model_path}")

        # 验证端口范围
        if params.port < 1024 or params.port > 65535:
            errors.append(f"Port must be between 1024 and 65535, got {params.port}")

        # 验证上下文长度
        if params.n_ctx < 1 or params.n_ctx > 32768:
            errors.append(f"Context length must be between 1 and 32768, got {params.n_ctx}")

        # 验证线程数
        cpu_count = os.cpu_count() or 1
        if params.n_threads < 1 or params.n_threads > cpu_count:
            errors.append(f"Threads must be between 1 and {cpu_count}, got {params.n_threads}")

        # 验证并发请求数
        if params.max_concurrent_requests < 1 or params.max_concurrent_requests > 1000:
            errors.append(f"Max concurrent requests must be between 1 and 1000, got {params.max_concurrent_requests}")

        # 验证速率限制
        if params.rate_limit_requests < 0 or params.rate_limit_requests > 10000:
            errors.append(f"Rate limit requests must be between 0 and 10000, got {params.rate_limit_requests}")

        if params.rate_limit_window < 1 or params.rate_limit_window > 3600:
            errors.append(f"Rate limit window must be between 1 and 3600 seconds, got {params.rate_limit_window}")

        return errors

    @staticmethod
    def validate_server_availability(host: str, port: int) -> bool:
        """验证服务器端口是否可用"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((host, port))
            sock.close()
            return result != 0  # 如果连接失败，则端口可用
        except:
            return False

    @staticmethod
    def validate_config_fields(config) -> List[str]:
        """验证配置字段"""
        errors = []

        # 检查所有必需字段
        if not config.model.path:
            errors.append("Model path is required")

        # 验证路径安全性
        if config.model.path and ".." in str(config.model.path):
            errors.append("Model path contains unsafe path traversal")

        # 验证API密钥格式
        if config.security.api_keys_file:
            api_keys_path = config.security.api_keys_file
            if not api_keys_path.exists():
                errors.append(f"API keys file does not exist: {api_keys_path}")

        # 验证TLS配置
        if config.tls.enabled:
            if not config.tls.cert_file or not config.tls.key_file:
                errors.append("Both cert_file and key_file must be provided when TLS is enabled")
            elif not config.tls.cert_file.exists() or not config.tls.key_file.exists():
                errors.append("TLS certificate or key file does not exist")

        return errors
```

## 验证标准

- [ ] 配置验证功能实现完整
- [ ] 启动配置验证支持
- [ ] 服务器可用性验证
- [ ] 配置字段验证
- [ ] 详细错误信息提供
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 验证配置参数安全性
- 防止配置注入攻击
- 验证路径安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12