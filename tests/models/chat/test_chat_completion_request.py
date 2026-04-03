import pytest
from pydantic import ValidationError
from llama.models.chat.chat_completion_request import ChatCompletionRequest
from llama.models.chat.chat_message import ChatMessage
from llama.models.chat.chat_role import ChatRole


class TestChatCompletionRequest:
    def test_valid_chat_completion_request_creation(self):
        """验证有效的ChatCompletionRequest创建"""
        message_data = {
            "role": ChatRole.USER,
            "content": "Hello, how are you?"
        }
        message = ChatMessage(**message_data)

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [message]
        }
        request = ChatCompletionRequest(**data)

        assert request.model == "gpt-3.5-turbo"
        assert len(request.messages) == 1
        assert request.messages[0].role == ChatRole.USER
        assert request.messages[0].content == "Hello, how are you?"

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        message_data = {
            "role": ChatRole.USER,
            "content": "Hello"
        }
        message = ChatMessage(**message_data)

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [message]
        }
        request = ChatCompletionRequest(**data)

        # 验证默认值
        assert request.frequency_penalty == 0.0
        assert request.logit_bias is None
        assert request.max_tokens is None
        assert request.n == 1
        assert request.presence_penalty == 0.0
        assert request.seed is None
        assert request.stop is None
        assert request.stream is False
        assert request.temperature == 1.0
        assert request.top_p == 1.0
        assert request.user is None
        assert request.tools is None
        assert request.tool_choice is None

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        message_data = {
            "role": ChatRole.USER,
            "content": "Hello"
        }
        message = ChatMessage(**message_data)

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [message],
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            ChatCompletionRequest(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        message_data = {
            "role": ChatRole.USER,
            "content": "Hello, how are you?"
        }
        message = ChatMessage(**message_data)

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [message]
        }
        original = ChatCompletionRequest(**data)
        json_str = original.model_dump_json()
        restored = ChatCompletionRequest.model_validate_json(json_str)

        assert original.model == restored.model
        assert len(restored.messages) == 1
        assert original.messages[0].role == restored.messages[0].role
        assert original.messages[0].content == restored.messages[0].content

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试空消息内容
        message_data = {
            "role": ChatRole.USER,
            "content": ""
        }
        message = ChatMessage(**message_data)

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [message]
        }
        request = ChatCompletionRequest(**data)
        assert request.messages[0].content == ""

        # 测试长消息内容
        long_content = "a" * 1000
        message_data["content"] = long_content
        message = ChatMessage(**message_data)
        data["messages"] = [message]
        request = ChatCompletionRequest(**data)
        assert request.messages[0].content == long_content

        # 测试长模型名称
        data["model"] = "a" * 100
        request = ChatCompletionRequest(**data)
        assert request.model == "a" * 100