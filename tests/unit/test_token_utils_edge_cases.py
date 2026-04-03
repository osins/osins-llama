import pytest
from llama.utils.token_utils import count_tokens, count_tokens_in_messages, count_completion_tokens
from llama.models.chat.chat_message import ChatMessage
from llama.models.chat.chat_role import ChatRole
from llama.exceptions import ValidationError


class TestTokenUtilsEdgeCases:
    """测试token_utils模块的边缘情况"""
    
    def test_chinese_text_token_count(self):
        """测试中文文本的token计算"""
        chinese_text = "你好世界，这是一段中文文本。"
        tokens = count_tokens(chinese_text)
        assert tokens > 0
        print(f"Chinese text '{chinese_text}' has {tokens} tokens")
    
    def test_emoji_token_count(self):
        """测试emoji的token计算"""
        emoji_text = "Hello! 👋 World 🌍"
        tokens = count_tokens(emoji_text)
        assert tokens > 0
        print(f"Emoji text '{emoji_text}' has {tokens} tokens")
    
    def test_very_long_text(self):
        """测试超长文本的token计算"""
        long_text = "Hello world. " * 100000  # 10万个句子
        tokens = count_tokens(long_text)
        assert tokens > 0
        print(f"Very long text has {tokens} tokens")
    
    def test_empty_string(self):
        """测试空字符串"""
        tokens = count_tokens("")
        assert tokens == 0
    
    def test_none_input(self):
        """测试None输入"""
        tokens = count_tokens(None)
        assert tokens == 0
    
    def test_non_string_input(self):
        """测试非字符串输入"""
        tokens = count_tokens(12345)
        assert tokens > 0  # 应该将数字转换为字符串再计算
    
    def test_messages_with_none_content(self):
        """测试消息中包含None内容"""
        messages = [
            ChatMessage(
                role=ChatRole.USER,
                content=None
            )
        ]
        tokens = count_tokens_in_messages(messages)
        # 应该处理None内容而不报错
        assert tokens >= 0
    
    def test_completion_with_none_prompt(self):
        """测试completion中None prompt"""
        tokens = count_completion_tokens(None)
        assert tokens == 0
    
    def test_completion_with_invalid_type(self):
        """测试completion中无效类型"""
        with pytest.raises(ValidationError):
            count_completion_tokens(123)  # 传入整数而非字符串或列表
    
    def test_messages_with_invalid_type(self):
        """测试消息列表中包含无效类型"""
        messages = [{"invalid": "structure"}]
        tokens = count_tokens_in_messages(messages)
        # 应该处理无效结构而不报错
        assert tokens >= 0
    
    def test_unicode_text(self):
        """测试Unicode文本"""
        unicode_text = "Unicode测试: café, naïve, résumé, mañana, niño"
        tokens = count_tokens(unicode_text)
        assert tokens > 0
        print(f"Unicode text '{unicode_text}' has {tokens} tokens")
    
    def test_special_characters(self):
        """测试特殊字符"""
        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?~`"
        tokens = count_tokens(special_text)
        assert tokens > 0
        print(f"Special chars '{special_text}' has {tokens} tokens")