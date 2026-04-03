import pytest
from pydantic import ValidationError
from llama.models.chat.chat_completion_chunk import ChatCompletionChunk
from llama.models.chat.chat_completion_chunk_choice import ChatCompletionChunkChoice
from llama.models.chat.chat_completion_delta import ChatCompletionDelta
from llama.models.chat.chat_role import ChatRole
from llama.models.common.usage import Usage


class TestChatCompletionChunk:
    def test_valid_chat_completion_chunk_creation(self):
        """验证有效的ChatCompletionChunk创建"""
        delta_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello"
        }
        delta = ChatCompletionDelta(**delta_data)

        choice_data = {
            "index": 0,
            "delta": delta
        }
        choice = ChatCompletionChunkChoice(**choice_data)

        data = {
            "id": "test-id",
            "created": 1234567890,
            "choices": [choice],
            "model": "gpt-3.5-turbo"
        }
        chunk = ChatCompletionChunk(**data)

        assert chunk.id == "test-id"
        assert len(chunk.choices) == 1
        assert chunk.choices[0].index == 0
        assert chunk.choices[0].delta.role == ChatRole.ASSISTANT
        assert chunk.choices[0].delta.content == "Hello"
        assert chunk.model == "gpt-3.5-turbo"

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        delta_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello"
        }
        delta = ChatCompletionDelta(**delta_data)

        choice_data = {
            "index": 0,
            "delta": delta
        }
        choice = ChatCompletionChunkChoice(**choice_data)

        usage_data = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        usage = Usage(**usage_data)

        data = {
            "id": "test-id",
            "created": 1234567890,
            "choices": [choice],
            "model": "gpt-3.5-turbo",
            "usage": usage
        }
        chunk = ChatCompletionChunk(**data)

        assert chunk.created == 1234567890
        assert chunk.object == "chat.completion.chunk"

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        delta_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello"
        }
        delta = ChatCompletionDelta(**delta_data)

        choice_data = {
            "index": 0,
            "delta": delta
        }
        choice = ChatCompletionChunkChoice(**choice_data)

        data = {
            "id": "test-id",
            "choices": [choice],
            "model": "gpt-3.5-turbo",
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            ChatCompletionChunk(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        delta_data = {
            "role": ChatRole.ASSISTANT,
            "content": "Hello"
        }
        delta = ChatCompletionDelta(**delta_data)

        choice_data = {
            "index": 0,
            "delta": delta
        }
        choice = ChatCompletionChunkChoice(**choice_data)

        data = {
            "id": "test-id",
            "created": 1234567890,
            "choices": [choice],
            "model": "gpt-3.5-turbo"
        }
        original = ChatCompletionChunk(**data)
        json_str = original.model_dump_json()
        restored = ChatCompletionChunk.model_validate_json(json_str)

        assert original.id == restored.id
        assert original.model == restored.model
        assert len(restored.choices) == 1
        assert original.choices[0].index == restored.choices[0].index

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试空内容
        delta_data = {
            "role": ChatRole.ASSISTANT,
            "content": ""
        }
        delta = ChatCompletionDelta(**delta_data)

        choice_data = {
            "index": 0,
            "delta": delta
        }
        choice = ChatCompletionChunkChoice(**choice_data)

        data = {
            "id": "",
            "created": 1234567890,
            "choices": [choice],
            "model": "gpt-3.5-turbo"
        }
        chunk = ChatCompletionChunk(**data)
        assert chunk.id == ""
        assert chunk.choices[0].delta.content == ""

        # 测试较长的ID
        long_id = "a" * 100
        data["id"] = long_id
        chunk = ChatCompletionChunk(**data)
        assert chunk.id == long_id