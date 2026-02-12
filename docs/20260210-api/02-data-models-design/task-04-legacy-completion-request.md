# Legacy Completion Request模型任务文档

## 任务概述
- **任务编号**: 4
- **任务名称**: Legacy Completion Request模型
- **文件路径**: `models/legacy/completion_request.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现CompletionRequest数据模型，用于表示Legacy Completion API的请求对象。该模型继承CompletionParams并可能包含额外的请求特定字段，严格遵循OpenAI Completions API规范。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 继承CompletionParams模型
- 遵循OpenAI API的CompletionRequest对象结构
- 使用Pydantic v2语法

## 实现规范
- 继承CompletionParams模型的所有字段
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法
- 与Chat模型完全隔离，不共享任何字段

## 代码实现
```python
# models/legacy/completion_request.py

from pydantic import BaseModel, ConfigDict
from .completion_params import CompletionParams

class CompletionRequest(CompletionParams):
    """
    Completion Request 数据模型
    表示 Legacy Completion API 的请求对象，严格遵循 OpenAI Completions API 规范。
    继承CompletionParams的所有字段，无额外字段。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API的CompletionRequest结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝
- 继承关系正确

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)
- [Completion Params模型文档](task-03-legacy-completion-params.md)

## 依赖关系
- 依赖: `models/legacy/completion_params.py`

## 备注
此模型为Legacy Completion层的请求模型，与ChatCompletion请求模型完全隔离。