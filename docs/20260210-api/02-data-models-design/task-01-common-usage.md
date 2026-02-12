# Common Usage模型任务文档

## 任务概述
- **任务编号**: 1
- **任务名称**: Common Usage模型
- **文件路径**: `models/common/usage.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现Usage数据模型，用于表示API调用的使用量统计信息。该模型需要严格遵循OpenAI API规范，包含prompt_tokens、completion_tokens和total_tokens字段。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 包含以下字段：
  - prompt_tokens: int - 提示令牌数
  - completion_tokens: int - 补全令牌数
  - total_tokens: int - 总令牌数
- 遵循OpenAI API的Usage对象结构
- 使用Pydantic v2语法

## 实现规范
- 字段类型必须为int
- 所有字段均为必需字段
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法

## 代码实现
```python
# models/common/usage.py

from pydantic import BaseModel, ConfigDict

class Usage(BaseModel):
    """
    Usage 数据模型
    表示 API 调用的使用量统计信息，严格遵循 OpenAI 官方 API Usage 对象格式。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API返回的Usage结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)

## 依赖关系
- 无前置依赖

## 备注
此模型为公共基础模型，将在所有API端点中复用。