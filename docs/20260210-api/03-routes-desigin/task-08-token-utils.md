# 任务08：token_utils.count_tokens函数

## 任务概述

- **任务编号**: 8
- **任务名称**: 实现token计算工具函数
- **文件路径**: `src/llama/utils/token_utils.py`
- **函数名称**: `count_tokens`, `count_tokens_in_messages`, `count_completion_tokens`
- **任务状态**: 待开发
- **优先级**: 中

## 任务描述

实现准确的token计数功能，使用与模型一致的tokenizer计算文本或消息中的token数量，确保在生成和聊天接口中token限制的准确性。

## 技术要求

- 使用与模型匹配的tokenizer进行token计数
- 支持单个文本字符串的token计数
- 支持消息列表的token计数（用于聊天接口）
- 处理各种内容类型（文本、结构化内容等）
- 返回准确的token数量

## 实现规范

- **输入**: 文本字符串或消息对象列表，模型路径
- **输出**: 整数类型的token数量
- 使用与模型相同的tokenizer确保一致性
- 处理结构化内容（如消息内容的parts）
- 提供专门接口计算completion请求的prompt token

## 代码实现示例

```python
from typing import List, Union
from transformers import AutoTokenizer
from src.llama.models.chat.chat_message import ChatMessage
import os

def count_tokens(text: str, model_path: str) -> int:
    """
    使用指定模型的tokenizer计算文本的token数量
    """
    tokenizer_path = model_path.replace(".gguf", "")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
    tokens = tokenizer.encode(text)
    return len(tokens)

def count_tokens_in_messages(messages: List[ChatMessage], model_path: str) -> int:
    """
    计算消息列表的总token数量
    """
    total_tokens = 0
    tokenizer_path = model_path.replace(".gguf", "")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
    
    for message in messages:
        # 编码头部信息
        total_tokens += len(tokenizer.encode(f"<|im_start|>{message.role.value}"))
        
        # 编码内容
        if isinstance(message.content, str):
            total_tokens += len(tokenizer.encode(message.content))
        else:
            # 处理结构化内容
            if hasattr(message.content, '__iter__'):
                for part in message.content:
                    if hasattr(part, 'text'):
                        total_tokens += len(tokenizer.encode(part.text))
                    elif isinstance(part, str):
                        total_tokens += len(tokenizer.encode(part))
        
        # 编码结束标记
        total_tokens += len(tokenizer.encode("<|im_end|>"))
    
    return total_tokens

def count_completion_tokens(prompt: str, model_path: str) -> int:
    """
    计算completion请求的prompt token数量
    """
    return count_tokens(prompt, model_path)
````

## 验证标准

- 函数能够准确计算单条文本的token数量
- 函数能够准确计算消息列表的token数量
- 与模型实际使用的tokenizer保持一致
- 正确处理结构化消息内容（含多part）
- 返回的token数量与模型实际处理一致

## 相关文档

- [API开发规范](../../2026021001-development-specification.md)
- [数据模型设计](../../../20260210-api/02-data-models-design/implementation-guide.md)

## 依赖关系

- `src/llama/models/chat/chat_message.py`
- `transformers`库
- `AutoTokenizer`

## 备注

- 确保tokenizer与模型路径一致
- 支持不同模型格式（如 GGUF）
- 可考虑缓存tokenizer实例优化性能
