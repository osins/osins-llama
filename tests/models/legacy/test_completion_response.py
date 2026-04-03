import pytest
from pydantic import ValidationError
from llama.models.legacy.completion_response import CompletionResponse
from llama.models.legacy.completion_choice import CompletionChoice
from llama.models.legacy.completion_finish_reason import CompletionFinishReason
from llama.models.common.usage import Usage


class TestCompletionResponse:
    def test_valid_completion_response_creation(self):
        """验证有效的CompletionResponse创建"""
        choice_data = {
            "text": "Generated text",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP
        }
        choice = CompletionChoice(**choice_data)

        usage_data = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        usage = Usage(**usage_data)

        data = {
            "id": "test-id",
            "model": "gpt-3.5-turbo",
            "created": 1234567890,
            "choices": [choice],
            "usage": usage
        }
        response = CompletionResponse(**data)

        assert response.id == "test-id"
        assert response.model == "gpt-3.5-turbo"
        assert response.created == 1234567890
        assert len(response.choices) == 1
        assert response.choices[0].text == "Generated text"
        assert response.choices[0].index == 0
        assert response.choices[0].finish_reason == CompletionFinishReason.STOP
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20
        assert response.usage.total_tokens == 30

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        choice_data = {
            "text": "Generated text",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP
        }
        choice = CompletionChoice(**choice_data)

        usage_data = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        usage = Usage(**usage_data)

        data = {
            "id": "test-id",
            "model": "gpt-3.5-turbo",
            "created": 1234567890,
            "choices": [choice],
            "usage": usage
        }
        response = CompletionResponse(**data)

        assert response.object == "text_completion"

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        choice_data = {
            "text": "Generated text",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP
        }
        choice = CompletionChoice(**choice_data)

        usage_data = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        usage = Usage(**usage_data)

        data = {
            "id": "test-id",
            "model": "gpt-3.5-turbo",
            "created": 1234567890,
            "choices": [choice],
            "usage": usage,
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            CompletionResponse(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        choice_data = {
            "text": "Serialization test text",
            "index": 1,
            "finish_reason": CompletionFinishReason.LENGTH
        }
        choice = CompletionChoice(**choice_data)

        usage_data = {
            "prompt_tokens": 5,
            "completion_tokens": 15,
            "total_tokens": 20
        }
        usage = Usage(**usage_data)

        data = {
            "id": "test-id",
            "model": "gpt-4",
            "created": 987654321,
            "choices": [choice],
            "usage": usage
        }
        original = CompletionResponse(**data)
        json_str = original.model_dump_json()
        restored = CompletionResponse.model_validate_json(json_str)

        assert original.id == restored.id
        assert original.model == restored.model
        assert original.created == restored.created
        assert len(restored.choices) == 1
        assert original.choices[0].text == restored.choices[0].text
        assert original.choices[0].index == restored.choices[0].index
        assert original.choices[0].finish_reason == restored.choices[0].finish_reason
        assert original.usage.prompt_tokens == restored.usage.prompt_tokens

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试最小长度ID和文本
        choice_data = {
            "text": "a",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP
        }
        choice = CompletionChoice(**choice_data)

        usage_data = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        usage = Usage(**usage_data)

        data = {
            "id": "a",
            "model": "gpt-3.5-turbo",
            "created": 1234567890,
            "choices": [choice],
            "usage": usage
        }
        response = CompletionResponse(**data)
        assert response.id == "a"
        assert response.choices[0].text == "a"

        # 测试长ID和模型名
        long_id = "a" * 100
        long_model = "model-" + "x" * 50
        data["id"] = long_id
        data["model"] = long_model
        response = CompletionResponse(**data)
        assert response.id == long_id
        assert response.model == long_model