import pytest
from pydantic import ValidationError
from src.llama.models.legacy.completion_stream_delta import CompletionStreamDelta
from src.llama.models.legacy.completion_finish_reason import CompletionFinishReason


class TestCompletionStreamDelta:
    def test_valid_completion_stream_delta_creation(self):
        """验证有效的CompletionStreamDelta创建"""
        data = {
            "text": "Stream text",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP
        }
        delta = CompletionStreamDelta(**data)

        assert delta.text == "Stream text"
        assert delta.index == 0
        assert delta.finish_reason == CompletionFinishReason.STOP

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        data = {
            "text": "Stream text",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP
        }
        delta = CompletionStreamDelta(**data)

        # CompletionStreamDelta的所有字段都是必需的，因此无需验证可选字段

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        data = {
            "text": "Stream text",
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP,
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            CompletionStreamDelta(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        data = {
            "text": "Serialization test text",
            "index": 1,
            "finish_reason": CompletionFinishReason.LENGTH
        }
        original = CompletionStreamDelta(**data)
        json_str = original.model_dump_json()
        restored = CompletionStreamDelta.model_validate_json(json_str)

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
        delta = CompletionStreamDelta(**data)
        assert delta.text == ""

        # 测试长文本
        long_text = "a" * 1000
        data = {
            "text": long_text,
            "index": 0,
            "finish_reason": CompletionFinishReason.STOP
        }
        delta = CompletionStreamDelta(**data)
        assert delta.text == long_text

        # 测试大索引值
        data = {
            "text": "Test text",
            "index": 999,
            "finish_reason": CompletionFinishReason.STOP
        }
        delta = CompletionStreamDelta(**data)
        assert delta.index == 999

        # 测试不同完成原因
        for reason in [CompletionFinishReason.STOP, CompletionFinishReason.LENGTH, CompletionFinishReason.CONTENT_FILTER]:
            data = {
                "text": "Test text",
                "index": 0,
                "finish_reason": reason
            }
            delta = CompletionStreamDelta(**data)
            assert delta.finish_reason == reason