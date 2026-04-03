import pytest
from llama.models.chat.chat_finish_reason import ChatFinishReason


class TestChatFinishReason:
    def test_enum_values(self):
        """验证枚举值"""
        assert ChatFinishReason.STOP.value == "stop"
        assert ChatFinishReason.LENGTH.value == "length"
        assert ChatFinishReason.TOOL_CALLS.value == "tool_calls"
        assert ChatFinishReason.CONTENT_FILTER.value == "content_filter"

    def test_enum_access(self):
        """验证枚举访问"""
        reasons = [reason.value for reason in ChatFinishReason]
        expected_reasons = ["stop", "length", "tool_calls", "content_filter"]
        assert sorted(reasons) == sorted(expected_reasons)

    def test_enum_serialization(self):
        """验证枚举序列化为字符串"""
        for reason in ChatFinishReason:
            assert isinstance(reason.value, str)
            assert reason.value in ["stop", "length", "tool_calls", "content_filter"]

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 验证每个枚举项的值长度
        for reason in ChatFinishReason:
            assert len(reason.value) > 0
            assert len(reason.value) <= 20  # 假设最大长度限制