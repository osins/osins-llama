# 路由设计高级实现规范

## 1. 接口统一与重用

### 1.1 流式与非流式逻辑抽象
- **目的**: 减少重复代码，提高可维护性
- **实现方式**:
  - 创建通用的响应处理器
  - 抽象公共的请求预处理逻辑
  - 使用策略模式处理流式与非流式响应差异

### 1.2 代码示例
```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Union
from src.llama.models.common.response import BaseResponse

class ResponseStrategy(ABC):
    @abstractmethod
    async def process(self, request_data, model_output):
        pass

class StreamingResponseStrategy(ResponseStrategy):
    async def process(self, request_data, model_output) -> AsyncGenerator[str, None]:
        # 流式响应处理逻辑
        async for chunk in model_output:
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

class NonStreamingResponseStrategy(ResponseStrategy):
    async def process(self, request_data, model_output) -> BaseResponse:
        # 非流式响应处理逻辑
        return BaseResponse(data=model_output)

class ResponseProcessor:
    def __init__(self, strategy: ResponseStrategy):
        self.strategy = strategy
    
    async def process(self, request_data, model_output):
        return await self.strategy.process(request_data, model_output)
```

## 2. 增强类型约束

### 2.1 类型注解规范
- 所有函数必须使用完整的类型注解
- 使用Union、Optional、Generic等高级类型特性
- 定义和使用类型别名以提高可读性

### 2.2 静态分析工具集成
- 集成mypy进行类型检查
- 集成pylint进行代码质量检查
- CI/CD流程中包含静态分析验证

### 2.3 代码示例
```python
from typing import Union, Optional, AsyncGenerator, Dict, Any
from pydantic import BaseModel

async def create_completion(
    request: CompletionRequest,
    config: Config
) -> Union[CompletionResponse, AsyncGenerator[str, None]]:
    """
    创建文本补全的路由处理函数
    
    Args:
        request: 完整的请求对象
        config: 服务配置对象
        
    Returns:
        CompletionResponse对象或流式响应生成器
    """
    # 实现逻辑
    pass

def validate_token_limits(
    prompt: str, 
    max_tokens: int,
    model_path: str
) -> bool:
    """
    验证token限制
    
    Args:
        prompt: 输入文本
        max_tokens: 最大token数限制
        model_path: 模型路径
        
    Returns:
        True if within limits, False otherwise
    """
    # 实现逻辑
    pass
```

## 3. 异常分层

### 3.1 自定义异常类定义
- ValidationError: 请求参数验证错误
- RateLimitError: 请求频率限制错误
- ServiceError: 服务内部错误
- ModelLoadError: 模型加载错误
- AuthenticationError: 认证错误

### 3.2 代码示例
```python
class APIError(Exception):
    """基础API异常类"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(APIError):
    """请求参数验证错误"""
    def __init__(self, message: str = "Invalid request parameters"):
        super().__init__(message, 400)

class RateLimitError(APIError):
    """请求频率限制错误"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, 429)

class ServiceError(APIError):
    """服务内部错误"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, 500)

class ModelLoadError(APIError):
    """模型加载错误"""
    def __init__(self, message: str = "Failed to load model"):
        super().__init__(message, 503)

class AuthenticationError(APIError):
    """认证错误"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)
```

### 3.3 统一异常处理
```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request

async def global_exception_handler(request: Request, exc: APIError):
    """
    全局异常处理器
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message
            }
        }
    )
```

## 4. 日志与监控

### 4.1 日志装饰器
- 记录请求参数
- 记录响应结果
- 记录异常信息
- 记录性能指标

### 4.2 代码示例
```python
import functools
import time
import logging
from typing import Callable, Any
from fastapi import Request

logger = logging.getLogger(__name__)

def log_api_call(func: Callable) -> Callable:
    """
    API调用日志装饰器
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        request = kwargs.get('request') or (args[0] if args else None)
        
        try:
            # 记录请求
            logger.info(f"API Call Started: {func.__name__}, Client: {getattr(request, 'client', 'Unknown')}")
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 记录成功响应
            logger.info(f"API Call Success: {func.__name__}, Time: {execution_time:.2f}s")
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            # 记录异常
            logger.error(f"API Call Failed: {func.__name__}, Time: {execution_time:.2f}s, Error: {str(e)}")
            raise
    
    return wrapper

# 使用示例
@log_api_call
async def create_completion(request: CompletionRequest) -> CompletionResponse:
    # 实现逻辑
    pass
```

## 5. 单元测试覆盖率要求

### 5.1 覆盖率标准
- 强制单元测试覆盖率 ≥ 90%
- 边界条件测试覆盖率 100%
- 异常处理逻辑覆盖率 100%

### 5.2 测试分类
- 正常路径测试
- 异常路径测试
- 边界条件测试
- 性能测试
- 集成测试

### 5.3 测试示例
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.llama.services.completion_service import CompletionService
from src.llama.exceptions import ValidationError, RateLimitError

@pytest.mark.asyncio
class TestCompletionService:
    async def test_generate_with_valid_request(self):
        """测试有效请求的生成"""
        service = CompletionService(config=MagicMock())
        request = MagicMock()
        
        # Mock模型管理器
        service.model_manager.generate = AsyncMock(return_value={"result": "success"})
        
        result = await service.generate(request)
        
        assert result is not None
        service.model_manager.generate.assert_called_once()

    async def test_generate_with_invalid_request_raises_error(self):
        """测试无效请求抛出异常"""
        service = CompletionService(config=MagicMock())
        request = MagicMock()
        
        # Mock token计算，触发验证错误
        with pytest.raises(ValidationError):
            # 模拟token超出限制的情况
            pass

    async def test_generate_with_rate_limit_exceeded(self):
        """测试请求超出限制时抛出异常"""
        service = CompletionService(config=MagicMock())
        request = MagicMock()
        
        with pytest.raises(RateLimitError):
            # 模拟速率限制超出的情况
            pass
```

## 6. 实施建议

### 6.1 逐步实施
1. 首先实现异常分层，因为这会影响大部分代码
2. 然后添加类型注解和静态分析工具
3. 接着重构流式/非流式逻辑
4. 最后添加日志装饰器和测试覆盖率检查

### 6.2 CI/CD 集成
- 在CI流程中集成mypy类型检查
- 在CI流程中集成pylint代码质量检查
- 在CI流程中检查测试覆盖率
- 只有通过所有检查才能合并代码