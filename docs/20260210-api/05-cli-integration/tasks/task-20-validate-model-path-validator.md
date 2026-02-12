# validate_model_path验证函数实现

## 概述

validate_model_path验证函数用于验证模型路径的有效性。

## 实现要求

1. 实现模型路径存在性验证
2. 验证路径是否为文件
3. 验证文件扩展名
4. 防止路径遍历攻击
5. 提供清晰的错误信息

## 代码实现

```python
from pydantic import field_validator
from pathlib import Path


@field_validator('model_path')
def validate_model_path(cls, v):
    """验证模型路径"""
    if v and not v.exists():
        raise ValueError(f'Model path does not exist: {v}')
    if v and not v.is_file():
        raise ValueError(f'Model path is not a file: {v}')
    if v and v.suffix.lower() != '.gguf':
        raise ValueError(f'Model file must have .gguf extension: {v}')
    # 防止路径遍历
    if v and ".." in str(v):
        raise ValueError("Model path cannot contain parent directory references (..)")
    return v
```

## 验证标准

- [ ] 验证函数实现正确
- [ ] 路径存在性验证
- [ ] 文件类型验证
- [ ] 扩展名验证
- [ ] 路径遍历防护
- [ ] 提供清晰的错误信息
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整

## 安全考虑

- 防止路径遍历攻击
- 验证文件扩展名
- 验证文件存在性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12