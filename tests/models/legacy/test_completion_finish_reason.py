import pytest
from src.llama.models.legacy.completion_finish_reason import CompletionFinishReason


class TestCompletionFinishReason:
    def test_enum_values(self):
        """验证枚举值"""
        assert CompletionFinishReason.STOP.value == "stop"
        assert CompletionFinishReason.LENGTH.value == "length"

    def test_enum_access(self):
        """验证枚举访问"""
        reasons = [reason.value for reason in CompletionFinishReason]
        expected_reasons = ["stop", "length", "content_filter"]
        assert sorted(reasons) == sorted(expected_reasons)

    def test_enum_serialization(self):
        """验证枚举序列化为字符串"""
        for reason in CompletionFinishReason:
            assert isinstance(reason.value, str)
            assert reason.value in ["stop", "length", "content_filter"]

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 验证每个枚举项的值长度
        for reason in CompletionFinishReason:
            assert len(reason.value) > 0
            assert len(reason.value) <= 20  # 假设最大长度限制