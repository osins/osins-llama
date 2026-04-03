import pytest
from pydantic import ValidationError
from llama.models.chat.chat_completion_choice import ChatCompletionChoice
from llama.models.chat.chat_message import ChatMessage
from llama.models.chat.chat_role import ChatRole
from llama.models.chat.chat_finish_reason import ChatFinishReason


class TestChatCompletionChoice:
    def test_valid_chat_completion_choice_creation(self):
        """验证有效的ChatCompletionChoice创建"""
        message_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello, how can I help you?"
        }
        message = ChatMessage(**message_data)

        data = {
            "index": 0,
            "message": message,
            "finish_reason": ChatFinishReason.STOP
        }
        choice = ChatCompletionChoice(**data)

        assert choice.index == 0
        assert choice.message.role == ChatRole.ASSISTANT
        assert choice.message.content == "Hello, how can I help you?"
        assert choice.finish_reason == ChatFinishReason.STOP

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        message_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello, how can I help you?"
        }
        message = ChatMessage(**message_data)

        data = {
            "index": 0,
            "message": message,
            "finish_reason": ChatFinishReason.STOP
        }
        choice = ChatCompletionChoice(**data)

        assert choice.logprobs is None

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        message_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello, how can I help you?"
        }
        message = ChatMessage(**message_data)

        data = {
            "index": 0,
            "message": message,
            "finish_reason": ChatFinishReason.STOP,
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            ChatCompletionChoice(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        message_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello, how can I help you?"
        }
        message = ChatMessage(**message_data)

        data = {
            "index": 0,
            "message": message,
            "finish_reason": ChatFinishReason.STOP
        }
        original = ChatCompletionChoice(**data)
        json_str = original.model_dump_json()
        restored = ChatCompletionChoice.model_validate_json(json_str)

        assert original.index == restored.index
        assert original.message.role == restored.message.role
        assert original.message.content == restored.message.content
        assert original.finish_reason == restored.finish_reason

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试索引为0
        message_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Test message"
        }
        message = ChatMessage(**message_data)

        data = {
            "index": 0,
            "message": message,
            "finish_reason": ChatFinishReason.STOP
        }
        choice = ChatCompletionChoice(**data)
        assert choice.index == 0

        # 测试较大的索引值
        data["index"] = 999
        choice = ChatCompletionChoice(**data)
        assert choice.index == 999