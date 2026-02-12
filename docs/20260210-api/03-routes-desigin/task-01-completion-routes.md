# 任务01：completion_routes.create_completion函数

## 任务概述

- **任务编号**: 1
- **任务名称**: 实现create_completion函数
- **文件路径**: `src/llama/api/completion_routes.py`
- **函数名称**: `create_completion`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述

实现 `/v1/completions` 路由的主要处理函数，负责接收请求、验证参数、调用服务层逻辑并返回符合 OpenAI API 规范的响应。

## 技术要求

- 使用 **FastAPI** 框架定义路由处理函数
- 使用 **Pydantic** 模型验证请求体
- 实现 **API Key 校验**
- 实现请求体长度与 token 数量校验
- 调用 `completion_service.generate()`
- 根据配置返回 **流式或完整响应**
- 统一错误处理机制

## 实现规范

- **路径**: `/v1/completions`
- **方法**: POST
- **请求体**: 使用 `CompletionRequest` 模型验证
- **响应**: 根据配置返回流式或非流式响应
- **错误处理**: 返回 JSON 格式错误，HTTP 状态码：
  - 400: 参数错误
  - 401: 未授权
  - 429: 排队超限
  - 504: 超时

## 代码实现示例

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import AsyncGenerator
import asyncio
from src.llama.models.legacy.completion_request import CompletionRequest
from src.llama.models.legacy.completion_response import CompletionResponse
from src.llama.services.completion_service import CompletionService
from src.llama.core.model_manager import ModelManager

router = APIRouter()

@router.post("/v1/completions", response_model=CompletionResponse)
async def create_completion(
    request: CompletionRequest,
    service: CompletionService = Depends(CompletionService.get_instance)
):
    """
    处理文本生成请求
    """
    try:
        # 调用服务层逻辑
        result = await service.generate(request)
        return result
    except Exception as e:
        # 统一错误处理
        raise HTTPException(status_code=500, detail=str(e))
````

## 验证标准

- 函数能够正确接收和处理请求
- 参数验证功能正常
- API Key 校验功能正常（如果启用）
- 服务层调用正常
- 响应格式符合 OpenAI API 规范
- 错误处理机制有效
- 支持流式和非流式响应

## 相关文档

- [API开发规范](../../2026021001-development-specification.md)
- [数据模型设计](../../../20260210-api/02-data-models-design/implementation-guide.md)

## 依赖关系

- `src/llama/models/legacy/completion_request.py`
- `src/llama/models/legacy/completion_response.py`
- `src/llama/services/completion_service.py`
- `src/llama/core/model_manager.py`

## 备注

- 需要确保与 OpenAI API 完全兼容
- 需要处理流式和非流式响应
