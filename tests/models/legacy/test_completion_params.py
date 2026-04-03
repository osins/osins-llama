import pytest
from pydantic import ValidationError
from llama.models.legacy.completion_params import CompletionParams


class TestCompletionParams:
    def test_valid_completion_params_creation(self):
        """验证有效的CompletionParams创建"""
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": "Hello, world!",
            "max_tokens": 100,
            "temperature": 0.7
        }
        params = CompletionParams(**data)

        assert params.model == "gpt-3.5-turbo"
        assert params.prompt == "Hello, world!"
        assert params.max_tokens == 100
        assert params.temperature == 0.7

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": "Hello"
        }
        params = CompletionParams(**data)

        # 验证默认值
        assert params.max_tokens == 16
        assert params.temperature == 1.0
        assert params.top_p == 1.0
        assert params.n == 1
        assert params.stream is False
        assert params.logprobs is None
        assert params.echo is False
        assert params.stop is None
        assert params.presence_penalty == 0.0
        assert params.frequency_penalty == 0.0
        assert params.best_of == 1
        assert params.logit_bias is None
        assert params.user is None

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": "Hello, world!",
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            CompletionParams(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        data = {
            "model": "gpt-4",
            "prompt": "Serialization test",
            "max_tokens": 50,
            "temperature": 0.5
        }
        original = CompletionParams(**data)
        json_str = original.model_dump_json()
        restored = CompletionParams.model_validate_json(json_str)

        assert original.model == restored.model
        assert original.prompt == restored.prompt
        assert original.max_tokens == restored.max_tokens
        assert original.temperature == restored.temperature

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试空提示
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": ""
        }
        params = CompletionParams(**data)
        assert params.prompt == ""

        # 测试长提示
        long_prompt = "a" * 1000
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": long_prompt
        }
        params = CompletionParams(**data)
        assert params.prompt == long_prompt

        # 测试边界温度值
        for temp in [0.0, 2.0]:  # 假设温度范围是0.0-2.0
            data = {
                "model": "gpt-3.5-turbo",
                "prompt": "Test prompt",
                "temperature": temp
            }
            params = CompletionParams(**data)
            assert params.temperature == temp

        # 测试边界max_tokens值
        for max_tokens in [1, 2048]:  # 假设合理的边界值
            data = {
                "model": "gpt-3.5-turbo",
                "prompt": "Test prompt",
                "max_tokens": max_tokens
            }
            params = CompletionParams(**data)
            assert params.max_tokens == max_tokens