import pytest
from pydantic import ValidationError
from src.llama.models.chat.tool_call import ToolCall
from src.llama.models.chat.tool_call_function import FunctionCall


class TestToolCall:
    def test_valid_tool_call_creation(self):
        """验证有效的ToolCall创建"""
        function_data = {
            "name": "get_current_weather",
            "arguments": '{"location": "Boston", "unit": "celsius"}'
        }
        function_call = FunctionCall(**function_data)

        data = {
            "id": "call_123456789",
            "function": function_call
        }
        tool_call = ToolCall(**data)

        assert tool_call.id == "call_123456789"
        assert tool_call.function.name == "get_current_weather"
        assert tool_call.function.arguments == '{"location": "Boston", "unit": "celsius"}'
        assert tool_call.type == "function"

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        function_data = {
            "name": "simple_func",
            "arguments": '{}'
        }
        function_call = FunctionCall(**function_data)

        data = {
            "id": "call_987654321",
            "function": function_call
        }
        tool_call = ToolCall(**data)

        assert tool_call.type == "function"

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        function_data = {
            "name": "test_func",
            "arguments": '{}'
        }
        function_call = FunctionCall(**function_data)

        data = {
            "id": "call_111111111",
            "function": function_call,
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            ToolCall(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        function_data = {
            "name": "get_weather",
            "arguments": '{"location": "New York"}'
        }
        function_call = FunctionCall(**function_data)

        data = {
            "id": "call_222222222",
            "function": function_call
        }
        original = ToolCall(**data)
        json_str = original.model_dump_json()
        restored = ToolCall.model_validate_json(json_str)

        assert original.id == restored.id
        assert original.function.name == restored.function.name
        assert original.function.arguments == restored.function.arguments
        assert original.type == restored.type

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试短ID
        function_data = {
            "name": "f",
            "arguments": '{}'
        }
        function_call = FunctionCall(**function_data)

        data = {
            "id": "c",
            "function": function_call
        }
        tool_call = ToolCall(**data)
        assert tool_call.id == "c"
        assert tool_call.function.name == "f"

        # 测试长ID和参数
        long_id = "a" * 100
        long_args = '{"param": "' + "x" * 500 + '"}'
        function_data = {
            "name": "long_function_name_here",
            "arguments": long_args
        }
        function_call = FunctionCall(**function_data)

        data = {
            "id": long_id,
            "function": function_call
        }
        tool_call = ToolCall(**data)
        assert tool_call.id == long_id
        assert len(tool_call.function.arguments) > 500