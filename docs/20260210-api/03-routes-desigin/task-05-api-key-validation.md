
# 任务05：security.verify_api_key函数

## 任务概述

- **任务编号**: 5
- **任务名称**: 实现verify_api_key函数
- **文件路径**: `src/llama/utils/security.py`
- **函数名称**: `verify_api_key`
- **任务状态**: 待开发
- **优先级**: 中

## 任务描述

实现 API Key 验证功能，用于验证传入请求的 API 密钥是否有效，确保只有授权用户才能访问 API 端点。

## 技术要求

- 从配置中获取允许的 API Key 列表
- 验证请求头中的 Authorization 字段
- 支持 Bearer Token 格式的 API Key
- 当 `require_api_key` 配置为 false 时跳过验证
- 验证失败时抛出 HTTPException(401)

## 实现规范

- **输入**: FastAPI HTTP 请求对象
- **输出**: 布尔值表示验证是否通过
- 验证失败时抛出 HTTPException(401)
- 支持多个有效 API Key
- 尊重配置中的 `require_api_key` 设置
- 提供用于 FastAPI 路由依赖的 checker 函数

## 代码实现示例

```python
from fastapi import HTTPException, Request
from src.llama.config.config import Config

async def verify_api_key(request: Request, config: Config) -> bool:
    """
    验证API Key是否有效
    """
    if not config.api.require_api_key:
        return True
    
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header is missing")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    api_key = auth_header[len("Bearer "):].strip()
    
    if api_key not in config.api.api_keys:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    return True

def get_api_key_checker(config: Config):
    """
    返回一个依赖项，用于FastAPI路由中的API Key验证
    """
    async def api_key_checker(request: Request):
        return await verify_api_key(request, config)
    
    return api_key_checker
````

## 验证标准

- 函数能够正确验证有效的 API Key
- 函数能够拒绝无效的 API Key
- 当 `require_api_key` 为 false 时跳过验证
- 正确处理 Bearer Token 格式
- 返回适当的 HTTP 401 错误
- 支持多个 API Key

## 相关文档

- [API开发规范](../../2026021001-development-specification.md)
- [安全审计协议](../../2026021100-financial-grade-zero-trust-model-security-audit-protocol.md)

## 依赖关系

- `src/llama/config/config.py`
- FastAPI 框架

## 备注

- 需要确保 API Key 的安全存储和传输
- 应考虑实现速率限制功能
- 需要在路由中正确集成此验证功能
