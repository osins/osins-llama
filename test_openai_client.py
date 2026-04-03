import asyncio
import json
from src.llama.core.llama_model_client import LlamaModelClient
import os

def test_openai_compatibility():
    """测试OpenAI API兼容功能"""
    
    # 设置模型路径（如果提供的话，否则跳过测试）
    model_path = os.environ.get('TEST_MODEL_PATH', './model.gguf')
    
    print("=== Llama Model Client OpenAI API 测试 ===")
    print(f"使用模型: {model_path}")
    
    # 首先检查模型文件是否存在
    if not os.path.exists(model_path):
        print(f"警告: 模型文件不存在: {model_path}")
        print("跳过实际API测试，展示API调用示例")
        
        print("\nAPI使用示例如下:")
        print("1. 模型聊天补全调用:")
        chat_example = {
            "model": "your-model-name",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "temperature": 0.7,
            "max_tokens": 150
        }
        print(json.dumps(chat_example, indent=2))
        
        print("\n2. 文本补全调用:")
        completion_example = {
            "model": "your-model-name",
            "prompt": "The future of AI is",
            "temperature": 0.7,
            "max_tokens": 100
        }
        print(json.dumps(completion_example, indent=2))
        
        print("\n3. 模型列表请求:")
        model_example = {}
        print("# 调用 client.models() 方法")
        
        return
    
    print("启动llama.cpp服务器...")
    
    # 创建客户端实例
    client = LlamaModelClient(model_path=model_path)
    
    # 尝试启动服务器
    if not client.start_server():
        print("无法启动llama.cpp服务器")
        return
    
    try:
        print("\n1. 测试模型列表 API...")
        models_response = client.models()
        print(f"模型列表: {models_response}")
        
        print("\n2. 测试聊天补全 API...")
        chat_data = {
            "model": "test-model",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        try:
            chat_response = client.chat_completions(chat_data)
            print(f"聊天响应: {json.dumps(chat_response, indent=2)[:200]}...")
        except Exception as e:
            print(f"聊天API错误: {e}")
        
        print("\n3. 测试文本补全 API...")
        completion_data = {
            "model": "test-model",
            "prompt": "The capital of France is",
            "temperature": 0.1,
            "max_tokens": 50
        }
        try:
            completion_response = client.completions(completion_data)
            print(f"补全响应: {json.dumps(completion_response, indent=2)[:200]}...")
        except Exception as e:
            print(f"补全API错误: {e}")
        
        print("\n4. 测试流式聊天补全 API...")
        try:
            stream_data = {
                "model": "test-model",
                "messages": [
                    {"role": "user", "content": "Count from 1 to 5."}
                ],
                "temperature": 0.1,
                "max_tokens": 50
            }
            print("流式响应:", end=" ")
            for chunk in client.stream_chat_completions(stream_data):
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        print(content, end="", flush=True)
            print()  # 换行
        except Exception as e:
            print(f"流式聊天API错误: {e}")
        
    finally:
        print("\n关闭llama.cpp服务器...")
        client.stop_server()


if __name__ == "__main__":
    test_openai_compatibility()