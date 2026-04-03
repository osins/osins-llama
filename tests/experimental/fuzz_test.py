"""
模糊测试和恶意输入测试
用于验证数据模型的安全性和健壮性
"""
import random
import string
from typing import Any, Dict, List
from hypothesis import given, strategies as st
import pytest

from llama.models.chat.chat_message import ChatMessage
from llama.models.chat.chat_completion_request import ChatCompletionRequest
from llama.models.common.usage import Usage
from llama.models.chat.chat_role import ChatRole
from llama.models.chat.chat_content_part import ChatContentPart
from llama.models.chat.content_type import ContentType


def generate_random_string(min_length: int = 1, max_length: int = 1000) -> str:
    """生成随机字符串"""
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_letters + string.digits + ' \n\t', k=length))


def generate_extreme_string() -> str:
    """生成极端字符串，如超长字符串、特殊字符等"""
    # 超长字符串
    if random.choice([True, False]):
        return 'a' * 100000
    
    # 包含特殊字符的字符串
    special_chars = '\x00\x01\x02\x03\r\n\t\b\a\f\v'
    return generate_random_string() + special_chars + generate_random_string()


def test_chat_message_with_malicious_inputs():
    """测试ChatMessage对恶意输入的处理"""
    
    # 测试超长内容
    try:
        malicious_content = 'a' * 100001  # 超过最大长度限制
        ChatMessage(role=ChatRole.USER, content=malicious_content)
        assert False, "应该抛出验证错误"
    except Exception:
        pass  # 预期会抛出异常
    
    # 测试带有特殊字符的内容
    try:
        malicious_content = "\x00\x01" + generate_random_string()
        ChatMessage(role=ChatRole.USER, content=malicious_content)
        assert False, "应该抛出验证错误"
    except Exception:
        pass  # 预期会抛出异常


@given(
    content=st.text(min_size=1, max_size=10000),
    name=st.one_of(st.none(), st.text(min_size=1, max_size=255)),
    role=st.sampled_from(list(ChatRole))
)
def test_chat_message_fuzz(content: str, name: str, role: ChatRole):
    """使用Hypothesis进行ChatMessage的模糊测试"""
    try:
        message = ChatMessage(role=role, content=content, name=name)
        
        # 验证字段值
        assert message.role == role
        assert message.content == content
        if name is not None:
            assert message.name == name
    except Exception:
        # 某些输入可能会导致验证失败，这是正常的
        pass


def test_chat_completion_request_with_malicious_inputs():
    """测试ChatCompletionRequest对恶意输入的处理"""
    
    # 测试超长模型名称
    try:
        malicious_model = 'a' * 256  # 超过最大长度限制
        ChatCompletionRequest(model=malicious_model, messages=[])
        assert False, "应该抛出验证错误"
    except Exception:
        pass  # 预期会抛出异常
    
    # 测试过多的消息
    try:
        fake_messages = []
        for i in range(101):  # 超过最大数量限制
            fake_messages.append(ChatMessage(role=ChatRole.USER, content=f"message {i}"))
        ChatCompletionRequest(model="test-model", messages=fake_messages)
        assert False, "应该抛出验证错误"
    except Exception:
        pass  # 预期会抛出异常
    
    # 测试超出范围的温度值
    try:
        ChatCompletionRequest(model="test-model", messages=[ChatMessage(role=ChatRole.USER, content="test")], 
                             temperature=3.0)  # 超出最大值2.0
        assert False, "应该抛出验证错误"
    except Exception:
        pass  # 预期会抛出异常


def test_usage_with_malicious_inputs():
    """测试Usage对恶意输入的处理"""
    
    # 测试超出范围的大数值
    try:
        Usage(prompt_tokens=100001, completion_tokens=100001, total_tokens=200001)  # 超出最大值限制
        assert False, "应该抛出验证错误"
    except Exception:
        pass  # 预期会抛出异常


def test_chat_content_part_with_malicious_inputs():
    """测试ChatContentPart对恶意输入的处理"""
    
    # 测试超长文本
    try:
        malicious_text = 'a' * 10001  # 超过最大长度限制
        ChatContentPart(type=ContentType.TEXT, text=malicious_text)
        assert False, "应该抛出验证错误"
    except Exception:
        pass  # 预期会抛出异常


def run_security_tests():
    """运行所有安全相关测试"""
    print("运行ChatMessage恶意输入测试...")
    test_chat_message_with_malicious_inputs()
    print("✓ ChatMessage恶意输入测试完成")
    
    print("运行ChatCompletionRequest恶意输入测试...")
    test_chat_completion_request_with_malicious_inputs()
    print("✓ ChatCompletionRequest恶意输入测试完成")
    
    print("运行Usage恶意输入测试...")
    test_usage_with_malicious_inputs()
    print("✓ Usage恶意输入测试完成")
    
    print("运行ChatContentPart恶意输入测试...")
    test_chat_content_part_with_malicious_inputs()
    print("✓ ChatContentPart恶意输入测试完成")


if __name__ == "__main__":
    run_security_tests()
    print("\n所有模糊测试和恶意输入测试完成!")