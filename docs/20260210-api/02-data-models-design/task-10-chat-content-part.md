# Chat Content Part模型任务文档

## 任务概述
- **任务编号**: 10
- **任务名称**: Chat Content Part模型
- **文件路径**: `models/chat/chat_content_part.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现ChatContentPart数据模型，用于表示Chat API中消息内容的部件。该模型需要严格遵循OpenAI Chat API规范，支持文本、图像等多种内容类型，不能简单使用str类型。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 包含以下字段：
  - type: ContentType - 内容类型枚举
  - text: Optional[str] - 文本内容（可选）
  - image_url: Optional[ImageUrl] - 图像URL（可选）
- 支持文本、图像等多种内容类型
- 遵循OpenAI API的ChatContentPart对象结构
- 使用Pydantic v2语法

## 实现规范
- content必须是结构化parts，不能是简单str
- 支持多种内容类型（text, image_url等）
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法
- 与Legacy Completion模型完全隔离

## 代码实现
```python
# models/chat/chat_content_part.py

from pydantic import BaseModel, ConfigDict
from typing import Literal, Union, Optional
from enum import Enum

class ContentType(str, Enum):
    """
    内容类型枚举
    """
    TEXT = "text"
    IMAGE_URL = "image_url"

class ImageDetail(str, Enum):
    """
    图像细节枚举
    """
    AUTO = "auto"
    LOW = "low"
    HIGH = "high"

class ImageUrl(BaseModel):
    """
    图像URL模型
    """
    model_config = ConfigDict(extra="forbid")
    
    url: str
    detail: Optional[ImageDetail] = ImageDetail.AUTO

class ChatContentPart(BaseModel):
    """
    Chat Content Part 数据模型
    表示 Chat API 中消息内容的部件，支持文本、图像等多种内容类型。
    不能简单使用 str 类型，必须是结构化 content parts。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    type: ContentType
    text: Optional[str] = None
    image_url: Optional[ImageUrl] = None
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API的ChatContentPart结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝
- 支持多种内容类型

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)

## 依赖关系
- 无前置依赖

## 备注
此模型是Chat API支持多模态内容的关键，必须严格按照OpenAI官方schema实现，不得进行任何优化。