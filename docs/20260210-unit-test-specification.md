# 单元测试开发规范

## 1. 测试目标

### 1.1 验证数据模型字段类型和必选性

- 验证所有必填字段是否正确设置
- 验证可选字段是否可以为空或为None
- 验证默认值是否正确应用
- 验证字段类型是否符合预期

### 1.2 验证序列化/反序列化完整性（JSON ↔ 对象）

- 验证对象序列化为JSON的正确性
- 验证JSON反序列化为对象的正确性
- 验证嵌套对象的序列化/反序列化完整性

### 1.3 验证默认值和可选值正确性

- 验证默认值是否按预期设置
- 验证可选字段在未提供时的行为

### 1.4 验证额外字段拒绝策略（extra="forbid"）

- 验证当提供未定义字段时是否抛出ValidationError
- 确保模型严格遵循定义的字段集合

### 1.5 验证枚举值限制（如ChatFinishReason）

- 验证枚举字段是否限制在定义的值范围内
- 验证非法枚举值是否抛出ValidationError

### 1.6 验证流式与非流式模型隔离

- 验证流式模型与非流式模型的字段差异
- 确保流式模型不包含非流式字段

### 1.7 验证工具调用字段/嵌套对象完整性

- 验证工具调用字段的结构完整性
- 验证嵌套对象是否正确构建

## 2. 测试结构

### 2.1 目录结构

### 2.2 文件命名规范

- 测试文件名格式：`test_[model_name].py`
- 测试类名格式：`Test[ModelName]`
- 测试方法名格式：`test_[specific_behavior]`

## 3. 测试内容规范

### 3.1 字段验证

```python
def test_required_fields_validation():
    """验证所有必填字段必须提供正确类型的值"""
    # 正常情况
    # 异常情况（缺少必填字段）
    # 类型错误情况

def test_optional_fields_validation():
    """验证可选字段可以为空或为None"""
    # 可选字段为None的情况
    # 可选字段为空字符串/空列表的情况

def test_default_values():
    """验证默认值必须生效"""
    # 不提供默认字段时，验证默认值
    # 提供默认字段时，验证覆盖值
```

### 3.2 JSON序列化/反序列化

```python
def test_serialization_to_json():
    """验证对象序列化为JSON"""
    # 正常序列化
    # 嵌套对象序列化

def test_deserialization_from_json():
    """验证JSON反序列化为对象"""
    # 正常反序列化
    # 嵌套对象反序列化

def test_serialization_consistency():
    """验证序列化/反序列化一致性"""
    # 序列化后反序列化，字段值保持一致
```

### 3.3 枚举值验证

```python
def test_enum_value_restrictions():
    """验证枚举字段必须限制在定义的值内"""
    # 合法枚举值
    # 非法枚举值应抛出ValidationError

def test_enum_serialization():
    """验证序列化时枚举为字符串"""
    # 枚举序列化为字符串
    # 字符串反序列化为枚举
```

### 3.4 额外字段拒绝

```python
def test_extra_field_rejection():
    """验证在模型初始化时加入未定义字段，应抛出ValidationError"""
    # 提供额外字段应抛出异常
    # 验证extra="forbid"配置生效
```

### 3.5 流式/非流式模型隔离

```python
def test_streaming_vs_non_streaming_models():
    """验证流式模型（delta/chunk）不允许包含非流式字段（如usage）"""
    # 流式模型不包含usage字段
    # 非流式模型包含usage字段
    # 流式模型部分字段可选
```

### 3.6 边界条件

```python
def test_boundary_conditions():
    """验证边界条件：空列表、空字符串、极值数字等"""
    # 空字符串
    # 空列表
    # 极值数字（0, 负数, 大数）
    # 特殊浮点值（0.0, 1.0）

def test_stop_field_variations():
    """验证stop字段为单个字符串 vs 字符串列表"""
    # 单个字符串
    # 字符串列表
    # None值

def test_tool_calls_empty_or_not():
    """验证工具调用嵌套为空或非空"""
    # 工具调用为空列表
    # 工具调用为非空列表
```

### 3.7 互依赖字段

```python
def test_dependent_fields():
    """验证互依赖字段的正确性"""
    # ChatCompletionChoice.finish_reason必须与ChatFinishReason匹配
    # ChatCompletionChunkChoice.delta必须为ChatCompletionDelta对象
    # tool_calls字段必须是列表且包含合法对象或为空
```

## 4. 测试工具与要求

### 4.1 测试框架

- 使用pytest作为统一测试框架
- 使用pytest.mark.parametrize进行参数化测试
- 使用pytest.raises验证异常情况

### 4.2 验证工具

- 使用pydantic.ValidationError捕获非法初始化
- 使用json.loads/json.dumps验证序列化
- 使用model.model_dump()和model.model_validate()验证Pydantic v2 API

### 4.3 每个模型的测试要求

每个模型至少包含以下测试用例：

- 1条正常用例：验证所有字段的正确设置
- 1条可选字段为空用例：验证None/空值处理
- 1条非法字段或额外字段用例：验证字段验证
- 1条边界值用例：验证边界条件
- 1条序列化用例：验证JSON序列化/反序列化
- 1条枚举验证用例：验证枚举值限制（如适用）

## 5. 输出规范

### 5.1 测试执行

- 所有测试必须通过`pytest --strict-markers`运行
- 测试覆盖率应达到90%以上
- 测试执行时间应在合理范围内

### 5.2 测试报告

输出应包含：

- 模型名称
- 测试项（字段验证/序列化/枚举/拒绝策略等）
- 是否通过
- 执行时间
- 覆盖率统计

### 5.3 测试断言

- 使用清晰的断言消息
- 验证具体的字段值
- 验证异常类型和消息

## 6. 测试示例模板

```python
import pytest
from pydantic import ValidationError
from src.llama.models.chat.chat_message import ChatMessage
from src.llama.models.chat.chat_role import ChatRole

class TestChatMessage:
    def test_valid_chat_message_creation(self):
        """验证有效的ChatMessage创建"""
        data = {
            "role": ChatRole.USER,
            "content": "Hello, world!"
        }
        message = ChatMessage(**data)
        
        assert message.role == ChatRole.USER
        assert message.content == "Hello, world!"

    def test_optional_fields_none(self):
        """验证可选字段为None的情况"""
        data = {
            "role": ChatRole.USER,
            "content": "Hello",
            "name": None
        }
        message = ChatMessage(**data)
        
        assert message.name is None

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        data = {
            "role": ChatRole.USER,
            "content": "Hello",
            "invalid_field": "should_fail"
        }
        
        with pytest.raises(ValidationError):
            ChatMessage(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        data = {
            "role": ChatRole.USER,
            "content": "Hello, world!"
        }
        original = ChatMessage(**data)
        json_str = original.model_dump_json()
        restored = ChatMessage.model_validate_json(json_str)
        
        assert original.role == restored.role
        assert original.content == restored.content

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试空内容
        data = {
            "role": ChatRole.USER,
            "content": ""
        }
        message = ChatMessage(**data)
        assert message.content == ""
```

这套规范确保了单元测试的完整性、一致性和可靠性，有助于提高代码质量和开发效率。
