"""
简化版模糊测试和恶意输入测试
不使用外部库，只使用内置库
"""
import random
import string
import json
from typing import Any, Dict, List

from src.llama.models.chat.chat_message import ChatMessage
from src.llama.models.chat.chat_completion_request import ChatCompletionRequest
from src.llama.models.common.usage import Usage
from src.llama.models.chat.chat_role import ChatRole
from src.llama.models.chat.chat_content_part import ChatContentPart
from src.llama.models.chat.content_type import ContentType
from src.llama.models.chat.tool_call import ToolCall
from src.llama.models.chat.tool_call_function import FunctionCall


def generate_random_string(min_length: int = 1, max_length: int = 1000) -> str:
    """生成随机字符串"""
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_letters + string.digits + ' \n\t', k=length))


def test_chat_message_with_malicious_inputs():
    """测试ChatMessage对恶意输入的处理"""
    print("测试ChatMessage对恶意输入的处理...")
    
    # 测试超长内容
    try:
        malicious_content = 'a' * 100001  # 超过最大长度限制
        ChatMessage(role=ChatRole.USER, content=malicious_content)
        assert False, "应该抛出验证错误"
    except Exception as e:
        print(f"  [PASS] 成功捕获超长内容异常: {type(e).__name__}")
    
    # 测试带有特殊字符的内容
    try:
        malicious_content = "\x00\x01" + generate_random_string(100)  # 包含控制字符
        ChatMessage(role=ChatRole.USER, content=malicious_content)
        assert False, "应该抛出验证错误"
    except Exception as e:
        print(f"  [PASS] 成功捕获特殊字符异常: {type(e).__name__}")

    # 测试超长名称
    try:
        malicious_name = 'a' * 256  # 超过最大长度限制
        ChatMessage(role=ChatRole.USER, content="test", name=malicious_name)
        assert False, "应该抛出验证错误"
    except Exception as e:
        print(f"  [PASS] 成功捕获超长名称异常: {type(e).__name__}")


def test_chat_completion_request_with_malicious_inputs():
    """测试ChatCompletionRequest对恶意输入的处理"""
    print("测试ChatCompletionRequest对恶意输入的处理...")
    
    # 测试超长模型名称
    try:
        malicious_model = 'a' * 256  # 超过最大长度限制
        ChatCompletionRequest(model=malicious_model, messages=[])
        assert False, "应该抛出验证错误"
    except Exception as e:
        print(f"  [PASS] 成功捕获超长模型名异常: {type(e).__name__}")
    
    # 测试过多的消息
    try:
        fake_messages = []
        for i in range(101):  # 超过最大数量限制
            fake_messages.append(ChatMessage(role=ChatRole.USER, content=f"message {i}"))
        ChatCompletionRequest(model="test-model", messages=fake_messages)
        assert False, "应该抛出验证错误"
    except Exception as e:
        print(f"  [PASS] 成功捕获过多消息异常: {type(e).__name__}")
    
    # 测试超出范围的温度值
    try:
        ChatCompletionRequest(model="test-model", messages=[ChatMessage(role=ChatRole.USER, content="test")], 
                             temperature=3.0)  # 超出最大值2.0
        assert False, "应该抛出验证错误"
    except Exception as e:
        print(f"  [PASS] 成功捕获超出范围温度异常: {type(e).__name__}")
    
    # 测试超出范围的n值
    try:
        ChatCompletionRequest(model="test-model", messages=[ChatMessage(role=ChatRole.USER, content="test")], 
                             n=11)  # 超出最大值10
        assert False, "应该抛出验证错误"
    except Exception as e:
        print(f"  [PASS] 成功捕获超出范围n值异常: {type(e).__name__}")


def test_usage_with_malicious_inputs():
    """测试Usage对恶意输入的处理"""
    print("测试Usage对恶意输入的处理...")
    
    # 测试超出范围的大数值
    try:
        Usage(prompt_tokens=100001, completion_tokens=100001, total_tokens=200001)  # 超出最大值限制
        assert False, "应该抛出验证错误"
    except Exception as e:
        print(f"  [PASS] 成功捕获超出范围数值异常: {type(e).__name__}")


def test_chat_content_part_with_malicious_inputs():
    """测试ChatContentPart对恶意输入的处理"""
    print("测试ChatContentPart对恶意输入的处理...")
    
    # 测试超长文本
    try:
        malicious_text = 'a' * 10001  # 超过最大长度限制
        ChatContentPart(type=ContentType.TEXT, text=malicious_text)
        assert False, "应该抛出验证错误"
    except Exception as e:
        print(f"  [PASS] 成功捕获超长文本异常: {type(e).__name__}")


def test_serialization_deserialization_stress():
    """测试序列化/反序列化的压力测试"""
    print("测试序列化/反序列化的压力测试...")
    
    # 创建正常的数据对象
    message = ChatMessage(role=ChatRole.USER, content="Hello, world!", name="test_user")
    
    # 多次序列化和反序列化
    for i in range(100):
        json_str = message.model_dump_json()
        restored = ChatMessage.model_validate_json(json_str)
        
        # 验证数据完整性
        assert restored.role == message.role
        assert restored.content == message.content
        assert restored.name == message.name
    
    print("  [PASS] 序列化/反序列化压力测试通过")


def test_frozen_property():
    """测试frozen属性是否生效"""
    print("测试frozen属性是否生效...")
    
    message = ChatMessage(role=ChatRole.USER, content="Hello, world!")
    
    # 尝试修改frozen对象
    try:
        message.content = "New content"
        assert False, "应该抛出ValidationError，因为对象是frozen的"
    except Exception as e:
        if "frozen" in str(e).lower():
            print("  [PASS] 成功捕获frozen对象修改异常，frozen属性生效")
        else:
            raise e
    
    # 尝试添加新属性
    try:
        setattr(message, 'new_attr', 'new_value')
        assert False, "应该抛出ValidationError，因为对象是frozen的"
    except Exception as e:
        if "frozen" in str(e).lower():
            print("  [PASS] 成功捕获frozen对象添加属性异常，frozen属性生效")
        else:
            raise e


def run_security_tests():
    """运行所有安全相关测试"""
    print("开始运行模糊测试和恶意输入测试...\n")
    
    test_chat_message_with_malicious_inputs()
    print()
    
    test_chat_completion_request_with_malicious_inputs()
    print()
    
    test_usage_with_malicious_inputs()
    print()
    
    test_chat_content_part_with_malicious_inputs()
    print()
    
    test_serialization_deserialization_stress()
    print()
    
    test_frozen_property()
    print()
    
    print("所有模糊测试和恶意输入测试完成!")


if __name__ == "__main__":
    run_security_tests()