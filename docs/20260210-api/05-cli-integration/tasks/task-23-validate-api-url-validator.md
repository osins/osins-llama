# validate_api_url验证函数实现

## 概述

validate_api_url验证函数用于验证API URL格式的有效性。

## 实现要求

1. 实现API URL格式验证
2. 使用正则表达式进行验证
3. 支持HTTP和HTTPS协议
4. 提供清晰的错误信息

## 代码实现

```python
from pydantic import field_validator
import re


@field_validator('api_url')
def validate_api_url(cls, v):
    """验证API URL格式"""
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, v):
        raise ValueError('Invalid API URL format')
    return v
```

## 验证标准

- [ ] 验证函数实现正确
- [ ] URL格式验证
- [ ] 协议验证
- [ ] 提供清晰的错误信息
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整

## 安全考虑

- 防止恶意URL注入
- 验证URL格式安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12