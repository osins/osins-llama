import pytest
from pydantic import ValidationError
from src.llama.models.common.usage import Usage


class TestUsage:
    def test_valid_usage_creation(self):
        """验证有效的Usage创建"""
        data = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        usage = Usage(**data)

        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        # Usage模型的所有字段都是必需的，因此无需验证可选字段

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        data = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            Usage(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        data = {
            "prompt_tokens": 5,
            "completion_tokens": 15,
            "total_tokens": 20
        }
        original = Usage(**data)
        json_str = original.model_dump_json()
        restored = Usage.model_validate_json(json_str)

        assert original.prompt_tokens == restored.prompt_tokens
        assert original.completion_tokens == restored.completion_tokens
        assert original.total_tokens == restored.total_tokens

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试最小值（零）
        data = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        usage = Usage(**data)
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

        # 测试较大值
        large_data = {
            "prompt_tokens": 1000000,
            "completion_tokens": 2000000,
            "total_tokens": 3000000
        }
        usage = Usage(**large_data)
        assert usage.prompt_tokens == 1000000
        assert usage.completion_tokens == 2000000
        assert usage.total_tokens == 3000000

        # 验证总token数等于前两者的和（在某些实现中可能自动计算，但这里我们测试给定值）
        assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens