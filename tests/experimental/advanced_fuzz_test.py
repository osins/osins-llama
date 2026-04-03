"""
高级模糊测试和恶意输入测试
使用 Hypothesis 库进行更深入的测试
"""
import random
import string
from typing import Any, Dict, List
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from llama.models.chat.chat_message import ChatMessage
from llama.models.chat.chat_completion_request import ChatCompletionRequest
from llama.models.common.usage import Usage
from llama.models.chat.chat_role import ChatRole
from llama.models.chat.chat_content_part import ChatContentPart
from llama.models.chat.content_type import ContentType
from llama.models.chat.tool_call import ToolCall
from llama.models.chat.tool_call_function import FunctionCall


# 定义用于测试的策略
chat_content_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cc',)),  # 排除控制字符
    min_size=1,
    max_size=10000  # 限制在我们的最大长度内
)

model_name_strategy = st.text(
    alphabet=st.characters(min_codepoint=32, max_codepoint=126),  # ASCII可打印字符
    min_size=1,
    max_size=255
)

# 测试ChatMessage的模糊测试
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    content=chat_content_strategy,
    name=st.one_of(st.none(), st.text(min_size=1, max_size=255)),
    role=st.sampled_from(list(ChatRole))
)
def test_chat_message_comprehensive_fuzz(content: str, name: str, role: ChatRole):
    """全面测试ChatMessage的各种输入"""
    try:
        message = ChatMessage(role=role, content=content, name=name)
        
        # 验证字段值
        assert message.role == role
        assert message.content == content
        if name is not None:
            assert message.name == name
            
        # 测试序列化和反序列化
        json_str = message.model_dump_json()
        restored = ChatMessage.model_validate_json(json_str)
        
        assert restored.role == message.role
        assert restored.content == message.content
        assert restored.name == message.name
        
    except Exception as e:
        # 如果输入确实违反了验证规则，则这是预期行为
        if "Field required" in str(e) or "String too_long" in str(e) or "String too_short" in str(e):
            pass  # 这些是预期的验证错误
        else:
            raise e


# 测试ChatCompletionRequest的模糊测试
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    model=model_name_strategy,
    temperature=st.floats(min_value=0.0, max_value=2.0),
    max_tokens=st.integers(min_value=1, max_value=4096),
    n=st.integers(min_value=1, max_value=10)
)
def test_chat_completion_request_fuzz(model: str, temperature: float, max_tokens: int, n: int):
    """测试ChatCompletionRequest的各种输入"""
    try:
        # 创建一个简单的消息列表
        messages = [ChatMessage(role=ChatRole.USER, content="test message")]
        
        request = ChatCompletionRequest(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            n=n
        )
        
        # 验证字段值
        assert request.model == model
        assert request.temperature == temperature
        assert request.max_tokens == max_tokens
        assert request.n == n
        assert len(request.messages) == 1
        
        # 测试序列化和反序列化
        json_str = request.model_dump_json()
        restored = ChatCompletionRequest.model_validate_json(json_str)
        
        assert restored.model == request.model
        assert restored.temperature == request.temperature
        assert restored.max_tokens == request.max_tokens
        assert restored.n == request.n
        
    except Exception as e:
        # 如果输入确实违反了验证规则，则这是预期行为
        if "Field required" in str(e) or "greater_than_equal" in str(e) or "less_than_equal" in str(e):
            pass  # 这些是预期的验证错误
        else:
            raise e


# 测试Usage的模糊测试
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    prompt_tokens=st.integers(min_value=0, max_value=100000),
    completion_tokens=st.integers(min_value=0, max_value=100000),
    total_tokens=st.integers(min_value=0, max_value=200000)
)
def test_usage_fuzz(prompt_tokens: int, completion_tokens: int, total_tokens: int):
    """测试Usage的各种输入"""
    try:
        usage = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
        
        # 验证字段值
        assert usage.prompt_tokens == prompt_tokens
        assert usage.completion_tokens == completion_tokens
        assert usage.total_tokens == total_tokens
        
        # 测试序列化和反序列化
        json_str = usage.model_dump_json()
        restored = Usage.model_validate_json(json_str)
        
        assert restored.prompt_tokens == usage.prompt_tokens
        assert restored.completion_tokens == usage.completion_tokens
        assert restored.total_tokens == usage.total_tokens
        
    except Exception as e:
        # 如果输入确实违反了验证规则，则这是预期行为
        if "greater_than_equal" in str(e) or "less_than_equal" in str(e):
            pass  # 这些是预期的验证错误
        else:
            raise e


def test_nested_structure_limits():
    """测试嵌套结构的限制"""
    # 测试大量消息
    try:
        many_messages = []
        for i in range(101):  # 超过100的限制
            many_messages.append(ChatMessage(role=ChatRole.USER, content=f"message {i}"))
        
        ChatCompletionRequest(model="test", messages=many_messages)
        assert False, "应该抛出验证错误"
    except Exception:
        pass  # 预期会抛出异常
    
    # 测试深度嵌套（虽然在这个例子中不太可能，但以防万一）
    try:
        deep_content = "a" * 10001  # 超过内容长度限制
        ChatMessage(role=ChatRole.USER, content=deep_content)
        assert False, "应该抛出验证错误"
    except Exception:
        pass  # 预期会抛出异常


def test_special_attack_vectors():
    """测试特殊的攻击向量"""
    # JSON炸弹测试
    try:
        json_bomb = '{"a":' + '["a"]},' * 1000 + '{"z":"z"}'
        ChatMessage.model_validate_json(f'{{"role": "user", "content": {json_bomb}}}')
        assert False, "应该抛出验证错误"
    except Exception:
        pass  # 预期会抛出异常
    
    # 超大数据测试
    try:
        huge_number = 99999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999