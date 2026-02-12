import pytest
from pydantic import ValidationError
from src.llama.models.chat.tool_call_function import FunctionCall


class TestFunctionCall:
    def test_valid_function_call_creation(self):
        """验证有效的FunctionCall创建"""
        data = {
            "name": "get_current_weather",
            "arguments": '{"location": "Boston", "unit": "celsius"}'
        }
        function_call = FunctionCall(**data)

        assert function_call.name == "get_current_weather"
        assert function_call.arguments == '{"location": "Boston", "unit": "celsius"}'

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        data = {
            "name": "simple_func",
            "arguments": "{}"
        }
        function_call = FunctionCall(**data)

        # FunctionCall只有必需字段，所以不需要验证可选字段

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        data = {
            "name": "test_func",
            "arguments": "{}",
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            FunctionCall(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        data = {
            "name": "get_weather",
            "arguments": '{"location": "New York"}'
        }
        original = FunctionCall(**data)
        json_str = original.model_dump_json()
        restored = FunctionCall.model_validate_json(json_str)

        assert original.name == restored.name
        assert original.arguments == restored.arguments

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试空参数
        data = {
            "name": "func",
            "arguments": ""
        }
        function_call = FunctionCall(**data)
        assert function_call.name == "func"
        assert function_call.arguments == ""

        # 测试长函数名和参数
        long_name = "a" * 100
        long_args = '{"param": "' + "x" * 500 + '"}'
        data = {
            "name": long_name,
            "arguments": long_args
        }
        function_call = FunctionCall(**data)
        assert function_call.name == long_name
        assert len(function_call.arguments) > 500

        # 测试特殊字符
        special_name = "func_with_underscores_and_numbers_123"
        special_args = '{"special_chars": "!@#$%^&*()"}'
        data = {
            "name": special_name,
            "arguments": special_args
        }
        function_call = FunctionCall(**data)
        assert function_call.name == special_name
        assert function_call.arguments == special_args