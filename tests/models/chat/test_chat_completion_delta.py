import pytest
from pydantic import ValidationError
from llama.models.chat.chat_completion_delta import ChatCompletionDelta
from llama.models.chat.chat_completion_tool_call_delta import ChatCompletionToolCallDelta
from llama.models.chat.chat_completion_tool_call_delta_function import ChatCompletionToolCallDeltaFunction
from llama.models.chat.chat_role import ChatRole


class TestChatCompletionDelta:
    def test_valid_chat_completion_delta_creation(self):
        """验证有效的ChatCompletionDelta创建"""
        data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello, how can I assist you?"
        }
        delta = ChatCompletionDelta(**data)

        assert delta.role == ChatRole.ASSISTANT
        assert delta.content == "Hello, how can I assist you?"
        assert delta.tool_calls is None

    def test_delta_with_tool_calls(self):
        """验证带工具调用的ChatCompletionDelta创建"""
        function_data = {
            "name": "get_current_weather",
            "arguments": '{"location": "Boston", "unit": "celsius"}'
        }
        function_call = ChatCompletionToolCallDeltaFunction(**function_data)

        tool_call_data = {
            "index": 0,
            "function": function_call
        }
        tool_call = ChatCompletionToolCallDelta(**tool_call_data)

        data = {
            "role": ChatRole.ASSISTANT,
            "tool_calls": [tool_call]
        }
        delta = ChatCompletionDelta(**data)

        assert delta.role == ChatRole.ASSISTANT
        assert delta.content is None
        assert delta.tool_calls is not None
        assert len(delta.tool_calls) == 1
        assert delta.tool_calls[0].index == 0
        assert delta.tool_calls[0].function.name == "get_current_weather"

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello"
        }
        delta = ChatCompletionDelta(**data)

        assert delta.role == ChatRole.ASSISTANT
        assert delta.content == "Hello"
        assert delta.tool_calls is None

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello",
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            ChatCompletionDelta(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello, how can I assist you?"
        }
        original = ChatCompletionDelta(**data)
        json_str = original.model_dump_json()
        restored = ChatCompletionDelta.model_validate_json(json_str)

        assert original.role == restored.role
        assert original.content == restored.content

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试空内容
        data = {
            "role": ChatRole.ASSISTANT,
            "content": ""
        }
        delta = ChatCompletionDelta(**data)
        assert delta.content == ""

        # 测试长内容
        long_content = "a" * 1000
        data["content"] = long_content
        delta = ChatCompletionDelta(**data)
        assert delta.content == long_content

        # 测试不同角色
        for role in [ChatRole.USER, ChatRole.ASSISTANT, ChatRole.SYSTEM, ChatRole.TOOL]:
            data = {
                "role": role,
                "content": "Test message"
            }
            delta = ChatCompletionDelta(**data)
            assert delta.role == role