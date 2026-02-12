import pytest
from pydantic import ValidationError
from src.llama.models.chat.chat_message import ChatMessage
from src.llama.models.chat.chat_role import ChatRole
from src.llama.models.chat.chat_content_part import ChatContentPart, ContentType
from src.llama.models.chat.tool_call import ToolCall
from src.llama.models.chat.tool_call_function import FunctionCall


class TestChatMessage:
    def test_valid_chat_message_creation_with_text(self):
        """验证有效的文本ChatMessage创建"""
        data = {
            "role": ChatRole.USER,
            "content": "Hello, world!"
        }
        message = ChatMessage(**data)

        assert message.role == ChatRole.USER
        assert message.content == "Hello, world!"
        assert message.name is None
        assert message.tool_calls is None
        assert message.tool_call_id is None

    def test_valid_chat_message_creation_with_content_parts(self):
        """验证带内容部件的ChatMessage创建"""
        content_part_data = {
            "type": ContentType.TEXT,
            "text": "Hello, world!"
        }
        content_part = ChatContentPart(**content_part_data)

        data = {
            "role": ChatRole.USER,
            "content": [content_part]
        }
        message = ChatMessage(**data)

        assert message.role == ChatRole.USER
        assert isinstance(message.content, list)
        assert len(message.content) == 1
        assert message.content[0].type == ContentType.TEXT
        assert message.content[0].text == "Hello, world!"

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        data = {
            "role": ChatRole.USER,
            "content": "Hello",
            "name": "John Doe"
        }
        message = ChatMessage(**data)

        assert message.role == ChatRole.USER
        assert message.content == "Hello"
        assert message.name == "John Doe"
        assert message.tool_calls is None
        assert message.tool_call_id is None

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

    def test_message_with_tool_calls(self):
        """验证带工具调用的ChatMessage创建"""
        function_data = {
            "name": "get_current_weather",
            "arguments": '{"location": "Boston", "unit": "celsius"}'
        }
        function_call = FunctionCall(**function_data)

        tool_call_data = {
            "id": "call_123456789",
            "function": function_call
        }
        tool_call = ToolCall(**tool_call_data)

        data = {
            "role": ChatRole.ASSISTANT,
            "content": "Checking weather...",
            "tool_calls": [tool_call]
        }
        message = ChatMessage(**data)

        assert message.role == ChatRole.ASSISTANT
        assert message.content == "Checking weather..."
        assert message.tool_calls is not None
        assert len(message.tool_calls) == 1
        assert message.tool_calls[0].id == "call_123456789"
        assert message.tool_calls[0].function.name == "get_current_weather"

    def test_message_with_tool_call_id(self):
        """验证带工具调用ID的ChatMessage创建"""
        data = {
            "role": ChatRole.TOOL,
            "content": "Weather in Boston is 22°C.",
            "tool_call_id": "call_123456789"
        }
        message = ChatMessage(**data)

        assert message.role == ChatRole.TOOL
        assert message.content == "Weather in Boston is 22°C."
        assert message.tool_call_id == "call_123456789"

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试空内容
        data = {
            "role": ChatRole.USER,
            "content": ""
        }
        message = ChatMessage(**data)
        assert message.content == ""

        # 测试长内容
        long_content = "a" * 1000
        data = {
            "role": ChatRole.USER,
            "content": long_content
        }
        message = ChatMessage(**data)
        assert message.content == long_content

        # 测试不同角色
        for role in [ChatRole.USER, ChatRole.ASSISTANT, ChatRole.SYSTEM, ChatRole.TOOL]:
            data = {
                "role": role,
                "content": "Test message"
            }
            message = ChatMessage(**data)
            assert message.role == role