# SecurityChecker类实现

## 概述

SecurityChecker类负责验证CLI操作的安全性，防止路径遍历、权限不足等安全问题。

## 实现要求

1. 实现文件权限检查功能
2. 实现路径遍历检查功能
3. 验证API密钥文件安全性
4. 验证模型路径安全性
5. 验证配置文件路径安全性

## 代码实现

```python
import stat
from pathlib import Path
from typing import List
import os


class SecurityChecker:
    """安全检查器"""

    @staticmethod
    def check_file_permissions(file_path: Path, required_perms: int) -> bool:
        """检查文件权限"""
        if not file_path.exists():
            return False
        file_stat = file_path.stat()
        return (file_stat.st_mode & required_perms) == required_perms

    @staticmethod
    def check_path_traversal(path: str) -> bool:
        """检查路径遍历攻击"""
        return ".." not in path and "../" not in path and "..\\" not in path

    @staticmethod
    def validate_api_keys_file(api_keys_file: Path) -> List[str]:
        """验证API密钥文件安全性"""
        errors = []

        if not api_keys_file.exists():
            errors.append(f"API keys file does not exist: {api_keys_file}")
            return errors

        # 检查是否为符号链接
        if api_keys_file.is_symlink():
            errors.append(f"API keys file is a symbolic link: {api_keys_file}")

        # 检查文件权限
        file_stat = api_keys_file.stat()
        if (file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH)) != 0:
            errors.append(f"API keys file has insecure permissions: {api_keys_file}")

        # 检查文件大小（防止大文件注入）
        if file_stat.st_size > 1024 * 1024:  # 1MB
            errors.append(f"API keys file is too large (>1MB): {api_keys_file}")

        return errors

    @staticmethod
    def validate_model_path(model_path: Path) -> List[str]:
        """验证模型路径安全性"""
        errors = []

        if not model_path.exists():
            errors.append(f"Model path does not exist: {model_path}")
            return errors

        if not model_path.is_file():
            errors.append(f"Model path is not a file: {model_path}")

        if model_path.suffix.lower() != '.gguf':
            errors.append(f"Model file must have .gguf extension: {model_path}")

        # 检查路径遍历
        if not SecurityChecker.check_path_traversal(str(model_path)):
            errors.append(f"Model path contains path traversal: {model_path}")

        # 检查文件权限
        if not os.access(model_path, os.R_OK):
            errors.append(f"Model file is not readable: {model_path}")

        return errors

    @staticmethod
    def validate_config_path(config_path: Path) -> List[str]:
        """验证配置文件路径安全性"""
        errors = []

        if not config_path.exists():
            errors.append(f"Config file does not exist: {config_path}")
            return errors

        if not config_path.is_file():
            errors.append(f"Config path is not a file: {config_path}")

        if config_path.suffix.lower() not in ['.yaml', '.yml', '.json']:
            errors.append(f"Config file must have .yaml, .yml, or .json extension: {config_path}")

        # 检查路径遍历
        if not SecurityChecker.check_path_traversal(str(config_path)):
            errors.append(f"Config path contains path traversal: {config_path}")

        # 检查文件权限
        if not os.access(config_path, os.R_OK):
            errors.append(f"Config file is not readable: {config_path}")

        return errors
```

## 验证标准

- [ ] 文件权限检查功能实现完整
- [ ] 路径遍历检查功能
- [ ] API密钥文件安全性验证
- [ ] 模型路径安全性验证
- [ ] 配置文件路径安全性验证
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 防止路径遍历攻击
- 验证文件权限
- 验证符号链接
- 检查文件大小限制

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12