import pytest
from pydantic import ValidationError
from src.llama.models.legacy.completion_request import CompletionRequest


class TestCompletionRequest:
    def test_valid_completion_request_creation(self):
        """验证有效的CompletionRequest创建"""
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": "Hello, world!",
            "max_tokens": 100,
            "temperature": 0.7
        }
        request = CompletionRequest(**data)

        assert request.model == "gpt-3.5-turbo"
        assert request.prompt == "Hello, world!"
        assert request.max_tokens == 100
        assert request.temperature == 0.7

    def test_inheritance_from_completion_params(self):
        """验证从CompletionParams继承的字段"""
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": "Hello, world!",
            "max_tokens": 100,
            "temperature": 0.7,
            "top_p": 0.9,
            "n": 1,
            "stream": False,
            "logprobs": 5,
            "echo": True,
            "stop": ["END"],
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5,
            "best_of": 1,
            "logit_bias": {"100": 0.5},
            "user": "test_user"
        }
        request = CompletionRequest(**data)

        # 验证继承的字段
        assert request.model == "gpt-3.5-turbo"
        assert request.prompt == "Hello, world!"
        assert request.max_tokens == 100
        assert request.temperature == 0.7
        assert request.top_p == 0.9
        assert request.n == 1
        assert request.stream is False
        assert request.logprobs == 5
        assert request.echo is True
        assert request.stop == ["END"]
        assert request.presence_penalty == 0.5
        assert request.frequency_penalty == 0.5
        assert request.best_of == 1
        assert request.logit_bias == {"100": 0.5}
        assert request.user == "test_user"

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": "Hello, world!",
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            CompletionRequest(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": "Hello, world!",
            "max_tokens": 100,
            "temperature": 0.7
        }
        original = CompletionRequest(**data)
        json_str = original.model_dump_json()
        restored = CompletionRequest.model_validate_json(json_str)

        assert original.model == restored.model
        assert original.prompt == restored.prompt
        assert original.max_tokens == restored.max_tokens
        assert original.temperature == restored.temperature

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": "Hello, world!"
        }
        request = CompletionRequest(**data)

        # 验证默认值
        assert request.max_tokens == 16
        assert request.temperature == 1.0
        assert request.top_p == 1.0
        assert request.n == 1
        assert request.stream is False
        assert request.logprobs is None
        assert request.echo is False
        assert request.stop is None
        assert request.presence_penalty == 0.0
        assert request.frequency_penalty == 0.0
        assert request.best_of == 1
        assert request.logit_bias is None
        assert request.user is None