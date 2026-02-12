# validate_host验证函数实现

## 概述

validate_host验证函数用于验证主机地址格式的有效性。

## 实现要求

1. 实现主机地址格式验证
2. 支持IP地址和域名格式
3. 使用正则表达式进行验证
4. 提供清晰的错误信息

## 代码实现

```python
from pydantic import field_validator
import re


@field_validator('host')
def validate_host(cls, v):
    """验证主机地址"""
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^localhost$|^(\d{1,3}\.){3}\d{1,3}|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]*(\.[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]*)*$'
    if not re.match(ip_pattern, v):
        raise ValueError('Invalid host format')
    return v
```

## 验证标准

- [ ] 验证函数实现正确
- [ ] 支持IP地址和域名格式
- [ ] 使用正则表达式进行验证
- [ ] 提供清晰的错误信息
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整

## 安全考虑

- 防止恶意主机名注入
- 验证主机名格式安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12