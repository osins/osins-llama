# validate_pid_file验证函数实现

## 概述

validate_pid_file验证函数用于验证PID文件路径的有效性。

## 实现要求

1. 实现PID文件路径验证
2. 防止路径遍历攻击
3. 验证父目录存在性
4. 提供清晰的错误信息

## 代码实现

```python
from pydantic import field_validator
from pathlib import Path


@field_validator('pid_file')
def validate_pid_file(cls, v):
    """验证PID文件路径"""
    # 防止路径遍历
    if ".." in str(v):
        raise ValueError("PID file path cannot contain parent directory references (..)")
    if v and not v.parent.exists():
        raise ValueError(f'Directory for PID file does not exist: {v.parent}')
    return v
```

## 验证标准

- [ ] 验证函数实现正确
- [ ] 路径遍历防护
- [ ] 父目录存在性验证
- [ ] 提供清晰的错误信息
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整

## 安全考虑

- 防止路径遍历攻击
- 验证目录存在性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12