import pytest
from llama.utils.token_utils import count_tokens, count_tokens_in_messages, count_completion_tokens
from llama.models.chat.chat_message import ChatMessage
from llama.models.chat.chat_role import ChatRole


def test_count_tokens():
    """测试基本token计数功能"""
    text = "Hello, world!"
    token_count = count_tokens(text)
    
    # "Hello, world!" 应该产生少量tokens
    assert token_count > 0
    assert isinstance(token_count, int)


def test_count_tokens_empty_string():
    """测试空字符串的token计数"""
    token_count = count_tokens("")
    assert token_count == 0


def test_count_tokens_in_messages_single_message():
    """测试单个消息的token计数"""
    message = ChatMessage(role=ChatRole.USER, content="Hello, how are you?")
    messages = [message]
    
    token_count = count_tokens_in_messages(messages)
    assert token_count > 0
    assert isinstance(token_count, int)


def test_count_tokens_in_messages_multiple_messages():
    """测试多个消息的token计数"""
    messages = [
        ChatMessage(role=ChatRole.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(role=ChatRole.USER, content="Hello, how are you?"),
        ChatMessage(role=ChatRole.ASSISTANT, content="I'm doing well, thank you!")
    ]
    
    token_count = count_tokens_in_messages(messages)
    assert token_count > 0
    assert isinstance(token_count, int)


def test_count_tokens_in_messages_dict_format():
    """测试字典格式消息的token计数"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    token_count = count_tokens_in_messages(messages)
    assert token_count > 0
    assert isinstance(token_count, int)


def test_count_completion_tokens_single_prompt():
    """测试单个prompt的token计数"""
    prompt = "Complete this sentence: Hello,"
    token_count = count_completion_tokens(prompt)
    
    assert token_count > 0
    assert isinstance(token_count, int)


def test_count_completion_tokens_multiple_prompts():
    """测试多个prompts的token计数"""
    prompts = [
        "Complete this sentence: Hello,",
        "Another prompt here"
    ]
    token_count = count_completion_tokens(prompts)
    
    assert token_count > 0
    assert isinstance(token_count, int)


def test_count_completion_tokens_empty_input():
    """测试空输入的token计数"""
    token_count = count_completion_tokens("")
    assert token_count == 0
    
    token_count = count_completion_tokens([])
    assert token_count == 0