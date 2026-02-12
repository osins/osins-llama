# validate_n_threads验证函数实现

## 概述

validate_n_threads验证函数用于验证线程数的有效性。

## 实现要求

1. 实现线程数范围验证
2. 验证不超过CPU核心数
3. 提供清晰的错误信息

## 代码实现

```python
from pydantic import field_validator
import os


@field_validator('n_threads')
def validate_n_threads(cls, v):
    """验证线程数不超过CPU核心数"""
    cpu_count = os.cpu_count() or 1
    if v > cpu_count:
        raise ValueError(f'n_threads ({v}) exceeds CPU count ({cpu_count})')
    if v < 1:
        raise ValueError(f'n_threads ({v}) must be at least 1')
    return v
```

## 验证标准

- [ ] 验证函数实现正确
- [ ] 线程数范围验证
- [ ] CPU核心数验证
- [ ] 提供清晰的错误信息
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整

## 安全考虑

- 防止过多线程导致资源耗尽
- 验证线程数合理性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12