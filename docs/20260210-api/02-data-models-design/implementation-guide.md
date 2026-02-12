# 数据模型设计实施指南

## 概述
本文档为开发人员提供数据模型设计的具体实施步骤和最佳实践，确保100% OpenAI兼容性。

## 准备工作

### 1. 环境设置
```bash
# 确保项目环境已配置
cd C:\works\llm\codes\osins-llama
pip install -r requirements.txt
```

### 2. 依赖库选择
推荐使用以下库来确保类型安全和序列化兼容性：
- Pydantic: 用于数据验证和序列化
- typing: 用于类型注解
- enum: 用于枚举定义

## 实施步骤

### 阶段1：公共基础模型（预计耗时：2小时）

#### 1.1 创建usage.py
```python
# models/common/usage.py
from pydantic import BaseModel

class Usage(BaseModel):
    """
    使用量统计数据模型
    严格遵循 OpenAI API 规范
    """
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

#### 1.2 创建error_response.py
```python
# models/common/error_response.py
from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    """
    错误响应数据模型
    必须 100% 符合 OpenAI 格式
    """
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None

class ErrorModel(BaseModel):
    error: ErrorResponse
```

### 阶段2：Legacy Completion模型（预计耗时：4小时）

#### 2.1 创建completion_params.py
```python
# models/legacy/completion_params.py
from pydantic import BaseModel, Field
from typing import Optional, Union, List

class CompletionParams(BaseModel):
    """
    通用生成参数数据模型
    包含 temperature, max_tokens 等参数
    严格遵循 OpenAI completions API 规范
    """
    model: str
    prompt: Union[str, List[str]]
    max_tokens: Optional[int] = 16
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    logprobs: Optional[int] = None
    echo: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    best_of: Optional[int] = 1
    logit_bias: Optional[dict] = None
    user: Optional[str] = None
```

#### 2.2 创建completion_request.py
```python
# models/legacy/completion_request.py
from .completion_params import CompletionParams

class CompletionRequest(CompletionParams):
    """
    文本生成请求数据模型
    严格遵循 OpenAI completions API 规范
    """
    pass  # 继承所有参数，无需额外字段
```

#### 2.3 创建completion_choice.py
```python
# models/legacy/completion_choice.py
from pydantic import BaseModel
from typing import Optional, Dict, Any

class CompletionChoice(BaseModel):
    """
    文本生成选择数据模型
    仅包含 text 输出字段
    """
    text: str
    index: int
    logprobs: Optional[Dict[str, Any]] = None
    finish_reason: str  # "stop", "length", "content_filter"
```

#### 2.4 创建completion_response.py
```python
# models/legacy/completion_response.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .completion_choice import CompletionChoice
from ..common.usage import Usage

class CompletionResponse(BaseModel):
    """
    文本生成响应数据模型
    包含 usage 信息
    """
    id: str
    object: str = "text_completion"
    created: int  # Unix timestamp
    model: str
    choices: List[CompletionChoice]
    usage: Usage
```

### 阶段3：Chat模型核心（预计耗时：6小时）

#### 3.1 创建chat_role.py
```python
# models/chat/chat_role.py
from enum import Enum

class ChatRole(str, Enum):
    """
    聊天角色枚举
    必须包含 'user', 'assistant', 'system', 'tool' 等值
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
```

#### 3.2 创建chat_content_part.py
```python
# models/chat/chat_content_part.py
from pydantic import BaseModel, Field
from typing import Literal, Union, Optional
from enum import Enum

class ContentType(str, Enum):
    TEXT = "text"
    IMAGE_URL = "image_url"

class ImageDetail(str, Enum):
    AUTO = "auto"
    LOW = "low"
    HIGH = "high"

class ImageUrl(BaseModel):
    url: str
    detail: Optional[ImageDetail] = ImageDetail.AUTO

class ChatContentPart(BaseModel):
    """
    聊天内容部件数据模型
    支持文本、图像等多种内容类型
    不能简单使用 str 类型
    """
    type: ContentType
    text: Optional[str] = None
    image_url: Optional[ImageUrl] = None
    
    class Config:
        # 确保字段验证严格
        extra = "forbid"
```

#### 3.3 创建tool_call.py
```python
# models/chat/tool_call.py
from pydantic import BaseModel
from typing import Optional
import json

class FunctionCall(BaseModel):
    """
    函数调用数据模型的一部分
    """
    name: str
    arguments: str  # JSON字符串

class ToolCall(BaseModel):
    """
    工具调用数据模型
    支持函数调用等功能
    """
    id: str
    type: str = "function"
    function: FunctionCall
```

#### 3.4 创建chat_message.py
```python
# models/chat/chat_message.py
from pydantic import BaseModel
from typing import Union, List, Optional
from .chat_role import ChatRole
from .chat_content_part import ChatContentPart

class ChatMessage(BaseModel):
    """
    聊天消息数据模型
    包含 role 和 content（结构化 parts）
    """
    role: ChatRole
    content: Union[str, List[ChatContentPart]]
    name: Optional[str] = None
    tool_calls: Optional[List['ToolCall']] = None
    tool_call_id: Optional[str] = None

# 解决循环引用
ToolCall.update_forward_refs()
```

### 阶段4：Chat Completion接口模型（预计耗时：4小时）

#### 4.1 创建chat_completion_choice.py
```python
# models/chat/chat_completion_choice.py
from pydantic import BaseModel
from typing import Optional, List
from .chat_message import ChatMessage

class ChatCompletionChoice(BaseModel):
    """
    聊天生成选择数据模型
    包含 message 和 finish_reason
    """
    index: int
    message: ChatMessage
    finish_reason: str  # "stop", "length", "tool_calls", "content_filter"
    logprobs: Optional[dict] = None
```

#### 4.2 创建chat_completion_request.py
```python
# models/chat/chat_completion_request.py
from pydantic import BaseModel, Field
from typing import Optional, Union, List, Dict, Any
from .chat_message import ChatMessage

class ChatCompletionRequest(BaseModel):
    """
    聊天生成请求数据模型
    严格遵循 OpenAI chat completions API 规范
    """
    messages: List[ChatMessage]
    model: str
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    max_tokens: Optional[int] = None
    n: Optional[int] = 1
    presence_penalty: Optional[float] = 0.0
    seed: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    user: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
```

#### 4.3 创建chat_completion_response.py
```python
# models/chat/chat_completion_response.py
from pydantic import BaseModel
from typing import List
from datetime import datetime
from .chat_completion_choice import ChatCompletionChoice
from ..common.usage import Usage

class ChatCompletionResponse(BaseModel):
    """
    聊天生成响应数据模型
    包含 choices 和 usage 信息
    """
    id: str
    object: str = "chat.completion"
    created: int  # Unix timestamp
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage
```

## 验证步骤

### 1. Schema校验测试
确保所有模型都启用了严格的字段校验：
```python
# 测试缺少必需字段是否会抛出异常
try:
    # 尝试创建缺少必需字段的对象
    invalid_obj = ChatMessage(role="user")  # 缺少content
except Exception as e:
    assert "field required" in str(e)
```

### 2. 类型兼容性测试
验证模型与OpenAI API的类型兼容性：
```python
# 验证枚举值
assert ChatRole.USER == "user"
assert ChatRole.ASSISTANT == "assistant"
assert ChatRole.SYSTEM == "system"
assert ChatRole.TOOL == "tool"
```

### 3. 序列化/反序列化测试
验证模型的序列化和反序列化功能：
```python
# 测试序列化
msg = ChatMessage(role=ChatRole.USER, content="Hello")
json_str = msg.json()

# 测试反序列化
parsed_msg = ChatMessage.parse_raw(json_str)
assert parsed_msg.role == ChatRole.USER
assert parsed_msg.content == "Hello"
```

## 注意事项

### 严格遵循OpenAI Schema
- 不要对OpenAI的API schema进行任何"改进"或"优化"
- 特别是在chat_content_part.py和tool_call.py中，必须完全照抄官方字段结构

### 避免常见错误
1. 不要在API层使用泛型
2. 不要混合使用Completion和Chat的模型
3. 不要让ErrorResponse依赖HTTP状态码
4. 不要在非流式响应中包含流式字段

### 性能考虑
- 使用Pydantic的validator进行复杂验证
- 避免在模型中包含不必要的计算逻辑
- 考虑使用Pydantic的Config设置来优化性能