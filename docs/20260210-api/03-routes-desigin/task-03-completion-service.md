
# 任务03：completion_service.CompletionService.generate函数

## 任务概述

- **任务编号**: 3
- **任务名称**: 实现CompletionService.generate函数
- **文件路径**: `src/llama/services/completion_service.py`
- **函数名称**: `CompletionService.generate`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述

实现 CompletionService 类的 `generate` 方法，处理文本生成请求的核心逻辑，包括 token 限制检查、调用模型管理器生成文本、结果格式化、流式和非流式响应处理，以及并发控制和排队机制。

## 技术要求

- 调用 `ModelManager.get_instance(config).generate()` 或 `generate_stream()`
- 对 prompt 做 token 限制检查
- 对生成结果进行 OpenAI API 兼容格式化
- 实现流式返回逻辑（按 token）
- 捕获模型生成异常，统一转换为 HTTP 错误
- 实现并发控制和排队机制

## 实现规范

- **输入**: `CompletionRequest` 对象
- **输出**: `CompletionResponse` 对象或异步生成器
- 遵循 OpenAI API 响应格式
- 实现 token 数量限制检查
- 实现流式和非流式响应处理

## 代码实现示例

```python
import asyncio
from typing import AsyncGenerator
from src.llama.models.legacy.completion_request import CompletionRequest
from src.llama.models.legacy.completion_response import CompletionResponse
from src.llama.core.model_manager import ModelManager
from src.llama.config.config import Config
from src.llama.utils.token_utils import count_tokens

class CompletionService:
    def __init__(self, config: Config):
        self.config = config
        self.model_manager = ModelManager.get_instance(config)
    
    @classmethod
    def get_instance(cls, config: Config):
        if not hasattr(cls, '_instance'):
            cls._instance = cls(config)
        return cls._instance
    
    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        """
        非流式文本生成
        """
        prompt_tokens = count_tokens(request.prompt, self.config.model.path)
        if prompt_tokens > self.config.resources.max_prompt_tokens:
            raise ValueError(f"Prompt exceeds maximum token count: {self.config.resources.max_prompt_tokens}")
        
        result = await self.model_manager.generate(request)
        
        response = CompletionResponse(
            id=result.get("id"),
            object="text_completion",
            created=result.get("created"),
            model=request.model,
            choices=result.get("choices"),
            usage=result.get("usage")
        )
        
        return response
    
    async def generate_stream(self, request: CompletionRequest) -> AsyncGenerator[str, None]:
        """
        流式文本生成
        """
        prompt_tokens = count_tokens(request.prompt, self.config.model.path)
        if prompt_tokens > self.config.resources.max_prompt_tokens:
            raise ValueError(f"Prompt exceeds maximum token count: {self.config.resources.max_prompt_tokens}")
        
        async for chunk in self.model_manager.generate_stream(request):
            yield f"data: {chunk}\n\n"
        
        yield "data: [DONE]\n\n"
````

## 验证标准

- 函数能够正确处理文本生成请求
- token 限制检查功能正常
- 模型调用功能正常
- 响应格式符合 OpenAI API 规范
- 流式响应处理正常
- 异常处理机制有效
- 并发控制按配置生效

## 相关文档

- [API开发规范](../../2026021001-development-specification.md)
- [数据模型设计](../../../20260210-api/02-data-models-design/implementation-guide.md)

## 依赖关系

- `src/llama/models/legacy/completion_request.py`
- `src/llama/models/legacy/completion_response.py`
- `src/llama/core/model_manager.py`
- `src/llama/config/config.py`
- `src/llama/utils/token_utils.py`

## 备注

- 需要确保与 OpenAI API 完全兼容
- 需要处理流式和非流式响应
- 需要考虑并发安全
