"""
测试模型管理器的流式生成功能
"""
import asyncio
import tempfile
import os
from pathlib import Path

# 创建一个假的 Llama 类用于测试
class MockLlama:
    def __call__(self, prompt, **kwargs):
        # 模拟模型生成响应
        return {
            "choices": [{
                "text": f"这是根据 '{prompt}' 生成的完整文本内容。",
                "index": 0,
                "finish_reason": "stop"
            }]
        }


def test_filter_llama_params():
    """测试参数过滤功能"""
    from src.llama.core.model_manager import filter_llama_params, LLAMA_VALID_PARAMS

    print("Testing parameter filtering...")
    
    # 测试参数过滤
    test_params = {
        'prompt': 'Test prompt',
        'max_tokens': 200,
        'temperature': 0.7,
        'n': 1,  # 不支持的参数
        'grammar': "",  # 空字符串，应被移除
        'logit_bias': [],  # 空列表，应被移除
        'stop': ['\n', 'END']
    }
    
    result = filter_llama_params(test_params)
    
    # 验证过滤结果
    for param in result:
        assert param in LLAMA_VALID_PARAMS, f"参数 {param} 不在白名单中"
    
    # 验证不支持的参数被移除
    assert 'n' not in result, "不支持的参数 'n' 应该被移除"
    assert 'grammar' not in result, "空字符串grammar应该被移除"
    assert 'logit_bias' not in result, "空列表logit_bias应该被移除"
    
    print("√ 参数过滤测试通过！")


async def test_stream_generate():
    """测试流式生成功能"""
    from src.llama.core.model_manager import ModelManager
    from unittest.mock import Mock
    import sys

    print("Testing stream generation...")
    
    # 创建一个临时配置对象
    class MockModelConfig:
        def __init__(self):
            self.path = "dummy/path"
            self.n_ctx = 2048
            self.n_threads = 4
            self.verbose = False

    class MockConfig:
        def __init__(self):
            self.model = MockModelConfig()
        
        @classmethod
        def from_env(cls):
            return cls()
    
    # 创建一个MockLlama实例
    mock_model = MockLlama()
    
    # 手动创建ModelManager实例并替换模型
    manager = object.__new__(ModelManager)  # 创建实例但不调用__init__
    manager.config = MockConfig()
    manager.model_path = "dummy/path"
    manager.model = mock_model  # 直接替换模型为mock
    
    # 测试流式生成
    chunks = []
    async for chunk in manager.stream_generate("测试提示词", {"max_tokens": 100, "temperature": 0.7}):
        chunks.append(chunk)
        print(f"Received chunk: '{chunk}'")
    
    # 验证生成了内容
    full_text = "".join(chunks)
    assert len(full_text) > 0, "应该生成一些文本内容"
    assert "测试提示词" in full_text, "生成的文本应该与提示词相关"
    
    print(f"√ 流式生成测试通过！生成了 {len(full_text)} 个字符")
    print(f"完整生成内容: {full_text}")


async def main():
    test_filter_llama_params()
    await test_stream_generate()
    print("\n所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())