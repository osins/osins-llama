# Legacy Completion Finish Reason模型任务文档

## 任务概述
- **任务编号**: 7
- **任务名称**: Legacy Completion Finish Reason模型
- **文件路径**: `models/legacy/completion_finish_reason.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现CompletionFinishReason枚举，用于表示Legacy Completion API的完成原因。该枚举需要严格遵循OpenAI Completions API规范，仅包含Completion API允许的值，与ChatCompletion的FinishReason枚举分离。

## 技术要求
- 使用Python Enum作为基类
- 包含以下枚举值：
  - STOP: "stop" - 达到自然停止点
  - LENGTH: "length" - 达到最大长度
  - CONTENT_FILTER: "content_filter" - 内容过滤器触发
- 遵循OpenAI API的CompletionFinishReason枚举结构
- 与ChatFinishReason枚举完全分离

## 实现规范
- 仅允许"stop", "length", "content_filter"值
- 不允许"tool_calls"值（这是Chat API专用）
- 使用StrEnum或继承str和Enum以支持JSON序列化
- 遵循100% OpenAI兼容策略
- 与ChatFinishReason枚举完全物理隔离

## 代码实现
```python
# models/legacy/completion_finish_reason.py

from enum import Enum

class CompletionFinishReason(str, Enum):
    """
    Completion Finish Reason 枚举
    表示 Legacy Completion API 的完成原因，严格遵循 OpenAI Completions API 规范。
    仅包含Completion API允许的值，与ChatFinishReason枚举完全分离。
    """
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
```

## 验证标准
- 枚举值与OpenAI官方API完全一致
- 仅包含允许的枚举值
- 不包含Chat API专用的值（如"tool_calls"）
- 通过单元测试验证枚举值正确性

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)

## 依赖关系
- 无前置依赖

## 备注
此枚举与ChatFinishReason完全分离，确保Completion API不会出现非法的finish_reason值。