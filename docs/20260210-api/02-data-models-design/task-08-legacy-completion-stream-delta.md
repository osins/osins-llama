# Legacy Completion Stream Delta模型任务文档

## 任务概述
- **任务编号**: 8
- **任务名称**: Legacy Completion Stream Delta模型
- **文件路径**: `models/legacy/completion_stream_delta.py`
- **任务状态**: 待开发
- **优先级**: 中

## 任务描述
实现CompletionStreamDelta数据模型，用于表示Legacy Completion API流式响应的增量数据。该模型需要严格遵循OpenAI Completions API流式响应规范，与非流式响应模型分离。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 包含以下字段：
  - text: str - 增量文本
  - index: int - 选择索引
  - finish_reason: Optional[CompletionFinishReason] - 完成原因（可选）
- 遵循OpenAI API的Completion Stream Delta对象结构
- 使用Pydantic v2语法

## 实现规范
- 与CompletionResponse模型完全分离
- 仅用于流式响应（stream=True）
- 不包含usage字段（仅在最终chunk中提供）
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法
- 与Chat流式模型完全隔离

## 代码实现
```python
# models/legacy/completion_stream_delta.py

from pydantic import BaseModel, ConfigDict
from typing import Optional
from .completion_finish_reason import CompletionFinishReason

class CompletionStreamDelta(BaseModel):
    """
    Completion Stream Delta 数据模型
    表示 Legacy Completion API 流式响应的增量数据，严格遵循 OpenAI Completions API 规范。
    与非流式响应模型完全分离，仅用于流式响应。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    text: str = ""
    index: int
    finish_reason: Optional[CompletionFinishReason] = None
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API的CompletionStreamDelta结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝
- 与非流式响应模型完全分离

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)
- [Completion Finish Reason模型文档](task-07-legacy-completion-finish-reason.md)

## 依赖关系
- 依赖: `models/legacy/completion_finish_reason.py`

## 备注
此模型用于支持Legacy Completion API的流式响应，与ChatCompletion流式模型完全隔离。