# Chat Role模型任务文档

## 任务概述
- **任务编号**: 9
- **任务名称**: Chat Role模型
- **文件路径**: `models/chat/chat_role.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现ChatRole枚举，用于表示Chat API中的角色类型。该枚举需要严格遵循OpenAI Chat API规范，包含user、assistant、system和tool等角色值。

## 技术要求
- 使用Python Enum作为基类
- 包含以下枚举值：
  - USER: "user" - 用户角色
  - ASSISTANT: "assistant" - 助手角色
  - SYSTEM: "system" - 系统角色
  - TOOL: "tool" - 工具角色
- 遵循OpenAI API的ChatRole枚举结构
- 支持JSON序列化

## 实现规范
- 必须包含'user', 'assistant', 'system', 'tool'角色以支持function/tool calling
- 使用StrEnum或继承str和Enum以支持JSON序列化
- 遵循100% OpenAI兼容策略
- 与Legacy Completion模型完全隔离

## 代码实现
```python
# models/chat/chat_role.py

from enum import Enum

class ChatRole(str, Enum):
    """
    Chat Role 枚举
    表示 Chat API 中的角色类型，严格遵循 OpenAI Chat API 规范。
    必须包含 'user', 'assistant', 'system', 'tool' 角色以支持 function/tool calling。
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
```

## 验证标准
- 枚举值与OpenAI官方API完全一致
- 包含所有必需的角色值
- 通过单元测试验证枚举值正确性
- 支持JSON序列化

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)

## 依赖关系
- 无前置依赖

## 备注
此枚举是Chat模型的核心组成部分，必须包含tool角色以支持function/tool calling功能。