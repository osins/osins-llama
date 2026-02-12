# PIDSecurityError异常类实现

## 概述

PIDSecurityError异常用于表示PID文件安全违规的情况。

## 实现要求

1. 定义PIDSecurityError异常类
2. 继承自ProcessError基类
3. 提供清晰的异常描述

## 代码实现

```python
"""Custom exceptions for CLI operations."""

class PIDSecurityError(Exception):
    """PID file security violation."""
    pass
```

## 验证标准

- [ ] 异常类定义正确
- [ ] 继承自ProcessError基类
- [ ] 提供清晰的异常描述
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整

## 安全考虑

- 无特殊安全考虑

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12