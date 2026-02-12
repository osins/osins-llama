# Legacy Completion Response模型任务文档

## 任务概述
- **任务编号**: 6
- **任务名称**: Legacy Completion Response模型
- **文件路径**: `models/legacy/completion_response.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现CompletionResponse数据模型，用于表示Legacy Completion API的完整响应对象。该模型需要严格遵循OpenAI Completions API规范，包含choices和usage信息。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 包含以下字段：
  - id: str - 响应ID
  - object: str - 对象类型（固定为"text_completion"）
  - created: int - 创建时间戳
  - model: str - 模型名称
  - choices: List[CompletionChoice] - 选择列表
  - usage: Usage - 使用量统计
- 遵循OpenAI API的CompletionResponse对象结构
- 使用Pydantic v2语法

## 实现规范
- object字段固定为"text_completion"
- choices字段为CompletionChoice对象列表
- usage字段为Usage对象（来自common模块）
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法
- 与Chat模型完全隔离，不共享任何Response模型

## 代码实现
```python
# models/legacy/completion_response.py

from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime
from .completion_choice import CompletionChoice
from ..common.usage import Usage

class CompletionResponse(BaseModel):
    """
    Completion Response 数据模型
    表示 Legacy Completion API 的完整响应对象，严格遵循 OpenAI Completions API 规范。
    与Chat模型完全隔离，不共享任何Response模型。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    id: str
    object: str = "text_completion"
    created: int  # Unix timestamp
    model: str
    choices: List[CompletionChoice]
    usage: Usage
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API的CompletionResponse结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝
- object字段默认值正确

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)
- [Completion Choice模型文档](task-05-legacy-completion-choice.md)
- [Usage模型文档](task-01-common-usage.md)

## 依赖关系
- 依赖: `models/legacy/completion_choice.py`
- 依赖: `models/common/usage.py`

## 备注
此模型为Legacy Completion层的响应模型，与ChatCompletion响应模型完全隔离。