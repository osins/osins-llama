import pytest
from pydantic import ValidationError
from src.llama.models.legacy.completion_choice import CompletionChoice
from src.llama.models.legacy.completion_finish_reason import CompletionFinishReason


class TestCompletionChoice:
    def test_valid_completion_choice_creation(self):
        """验证有效的CompletionChoice创建"""
        data = {
            "text": "Generated text",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP
        }
        choice = CompletionChoice(**data)

        assert choice.text == "Generated text"
        assert choice.index == 0
        assert choice.finish_reason == CompletionFinishReason.STOP

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        data = {
            "text": "Generated text",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP,
            "logprobs": None
        }
        choice = CompletionChoice(**data)

        assert choice.logprobs is None

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        data = {
            "text": "Generated text",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP,
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            CompletionChoice(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        data = {
            "text": "Serialization test text",
            "index": 1,
            "finish_reason": CompletionFinishReason.LENGTH
        }
        original = CompletionChoice(**data)
        json_str = original.model_dump_json()
        restored = CompletionChoice.model_validate_json(json_str)

        assert original.text == restored.text
        assert original.index == restored.index
        assert original.finish_reason == restored.finish_reason

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试空文本
        data = {
            "text": "",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP
        }
        choice = CompletionChoice(**data)
        assert choice.text == ""

        # 测试长文本
        long_text = "a" * 1000
        data = {
            "text": long_text,
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP
        }
        choice = CompletionChoice(**data)
        assert choice.text == long_text

        # 测试大索引值
        data = {
            "text": "Test text",
            "index": 999,
            "finish_reason": CompletionFinishReason.STOP
        }
        choice = CompletionChoice(**data)
        assert choice.index == 999

        # 测试不同完成原因
        for reason in [CompletionFinishReason.STOP, CompletionFinishReason.LENGTH]:
            data = {
                "text": "Test text",
                "index": 0,
                "finish_reason": reason
            }
            choice = CompletionChoice(**data)
            assert choice.finish_reason == reason