# Common Error Response模型任务文档

## 任务概述
- **任务编号**: 2
- **任务名称**: Common Error Response模型
- **文件路径**: `models/common/error_response.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现ErrorResponse数据模型，用于表示API调用的错误响应信息。该模型需要严格遵循OpenAI API规范，确保HTTP状态码与error.type解耦。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 包含以下字段：
  - message: str - 错误消息
  - type: str - 错误类型
  - param: Optional[str] - 参数名称（可选）
  - code: Optional[str] - 错误代码（可选）
- 遵循OpenAI API的ErrorResponse对象结构
- 使用Pydantic v2语法

## 实现规范
- message和type字段为必需字段
- param和code字段为可选字段
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法
- HTTP状态码 ≠ error.type，允许HTTP 200时返回error

## 代码实现
```python
# models/common/error_response.py

from pydantic import BaseModel, ConfigDict
from typing import Optional

class ErrorResponse(BaseModel):
    """
    Error Response 数据模型
    表示 API 调用的错误响应信息，严格遵循 OpenAI 官方 API Error Response 对象格式。
    HTTP状态码与error.type解耦，允许HTTP 200时返回error。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None

class ErrorModel(BaseModel):
    """
    Error包装模型
    """
    model_config = ConfigDict(extra="forbid")
    
    error: ErrorResponse
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API返回的ErrorResponse结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝
- 支持HTTP 200时返回error的情况

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)

## 依赖关系
- 无前置依赖

## 备注
此模型为公共基础模型，将在所有API端点中复用，确保错误处理的一致性。