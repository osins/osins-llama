import pytest
from pydantic import ValidationError
from src.llama.models.chat.chat_completion_response import ChatCompletionResponse
from src.llama.models.chat.chat_completion_choice import ChatCompletionChoice
from src.llama.models.chat.chat_message import ChatMessage
from src.llama.models.chat.chat_role import ChatRole
from src.llama.models.chat.chat_finish_reason import ChatFinishReason
from src.llama.models.common.usage import Usage


class TestChatCompletionResponse:
    def test_valid_chat_completion_response_creation(self):
        """验证有效的ChatCompletionResponse创建"""
        message_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello, how can I help you?"
        }
        message = ChatMessage(**message_data)

        choice_data = {
            "index": 0,
            "message": message,
            "finish_reason": ChatFinishReason.STOP
        }
        choice = ChatCompletionChoice(**choice_data)

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
        response = ChatCompletionResponse(**data)

        assert response.id == "test-id"
        assert response.model == "gpt-3.5-turbo"
        assert len(response.choices) == 1
        assert response.choices[0].index == 0
        assert response.choices[0].message.role == ChatRole.ASSISTANT
        assert response.choices[0].message.content == "Hello, how can I help you?"
        assert response.choices[0].finish_reason == ChatFinishReason.STOP
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20
        assert response.usage.total_tokens == 30

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        message_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello"
        }
        message = ChatMessage(**message_data)

        choice_data = {
            "index": 0,
            "message": message,
            "finish_reason": ChatFinishReason.STOP
        }
        choice = ChatCompletionChoice(**choice_data)

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
        response = ChatCompletionResponse(**data)

        assert response.created == 1234567890
        assert response.object == "chat.completion"

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        message_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello"
        }
        message = ChatMessage(**message_data)

        choice_data = {
            "index": 0,
            "message": message,
            "finish_reason": ChatFinishReason.STOP
        }
        choice = ChatCompletionChoice(**choice_data)

        data = {
            "id": "test-id",
            "model": "gpt-3.5-turbo",
            "choices": [choice],
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            ChatCompletionResponse(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        message_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello, how can I help you?"
        }
        message = ChatMessage(**message_data)

        choice_data = {
            "index": 0,
            "message": message,
            "finish_reason": ChatFinishReason.STOP
        }
        choice = ChatCompletionChoice(**choice_data)

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
        original = ChatCompletionResponse(**data)
        json_str = original.model_dump_json()
        restored = ChatCompletionResponse.model_validate_json(json_str)

        assert original.id == restored.id
        assert original.model == restored.model
        assert len(restored.choices) == 1
        assert original.choices[0].index == restored.choices[0].index
        assert original.choices[0].message.content == restored.choices[0].message.content
        assert original.usage.prompt_tokens == restored.usage.prompt_tokens

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试最小有效ID
        message_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello"
        }
        message = ChatMessage(**message_data)

        choice_data = {
            "index": 0,
            "message": message,
            "finish_reason": ChatFinishReason.STOP
        }
        choice = ChatCompletionChoice(**choice_data)

        usage_data = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        usage = Usage(**usage_data)

        # 测试最小长度ID
        data = {
            "id": "a",
            "model": "gpt-3.5-turbo",
            "created": 1234567890,
            "choices": [choice],
            "usage": usage
        }
        response = ChatCompletionResponse(**data)
        assert response.id == "a"
        assert response.usage.prompt_tokens == 0

        # 测试长ID
        long_id = "a" * 100
        data["id"] = long_id
        response = ChatCompletionResponse(**data)
        assert response.id == long_id