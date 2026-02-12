import pytest
from src.llama.models.chat.chat_role import ChatRole


class TestChatRole:
    def test_enum_values(self):
        """验证枚举值"""
        assert ChatRole.USER.value == "user"
        assert ChatRole.ASSISTANT.value == "assistant"
        assert ChatRole.SYSTEM.value == "system"
        assert ChatRole.TOOL.value == "tool"

    def test_enum_access(self):
        """验证枚举访问"""
        roles = [role.value for role in ChatRole]
        expected_roles = ["user", "assistant", "system", "tool"]
        assert sorted(roles) == sorted(expected_roles)

    def test_enum_serialization(self):
        """验证枚举序列化为字符串"""
        for role in ChatRole:
            assert isinstance(role.value, str)
            assert role.value in ["user", "assistant", "system", "tool"]

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 验证每个枚举项的值长度
        for role in ChatRole:
            assert len(role.value) > 0
            assert len(role.value) <= 20  # 假设最大长度限制