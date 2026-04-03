"""
OpenAI API 兼容性验证和接口可用性测试

此脚本演示如何启动服务以及验证各端点的可用性
"""

def test_openai_compatible_apis():
    print("=== OpenAI API 验证指南 ===")
    print()
    
    print("1. 启动 llama.cpp 服务")
    print("   首先需要有 gguf 格式的模型文件 (例如 mistral-7b.gguf)")
    print("   用法:")
    print("   $ llama start -m /path/to/model.gguf --port 31301")
    print()

    print("2. API 接口可用性验证")
    print("   使用 curl 测试各端点:")
    print()
    
    # 演示不同的 API 端点使用方法
    print("   a) 获取模型列表:")
    print("      curl http://127.0.0.1:31301/v1/models")
    print()
    
    print("   b) 聊天补全 API:")
    print("      curl -X POST http://127.0.0.1:31301/v1/chat/completions \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{")
    print('            "model": "your-model-name",')
    print('            "messages": [')
    print('                {"role": "system", "content": "You are a helpful assistant."},')
    print('                {"role": "user", "content": "Hello!"}')
    print('            ],')
    print('            "temperature": 0.7,')
    print('            "max_tokens": 150')
    print("        }'")
    print()
    
    print("   c) 文本补全 API:")
    print("      curl -X POST http://127.0.0.1:31301/v1/completions \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{")
    print('            "model": "your-model-name",')
    print('            "prompt": "The future of artificial intelligence",')
    print('            "temperature": 0.7,')
    print('            "max_tokens": 100')
    print("        }'")
    print()
    
    print("   d) 嵌入向量 API (示例):")
    print("      curl -X POST http://127.0.0.1:31301/v1/embeddings \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{")
    print('            "model": "your-model-name",')
    print('            "input": "Hello world"')
    print("        }'")
    print()
    
    print("3. Python 代码调用示例")
    print()
    print("   import requests")
    print("   url = 'http://127.0.0.1:31301/v1/chat/completions'")
    print("   payload = {")
    print('       "model": "llama",')
    print('       "messages": [{"role": "user", "content": "Hello!"}],')
    print('       "temperature": 0.7,')
    print('       "max_tokens": 50')
    print("   }")
    print("   response = requests.post(url, json=payload)")
    print("   print(response.json())")
    print()
    
    print("4. SDK 调用示例")
    print()
    print("   由于实现了 OpenAI API 兼容接口，您可以用 OpenAI SDK:")
    print()
    print("   from openai import OpenAI")
    print("   client = OpenA(base_url='http://127.0.0.1:31301/v1', api_key='dummy')")
    print()
    print("   # 聊天模式")
    print("   response = client.chat.completions.create(")
    print("       model='llama',")
    print("       messages=[{\"role\": \"user\", \"content\": \"Hello\"}],")
    print("       temperature=0.7,")
    print("       max_tokens=50")
    print("   )")
    print("   print(response.choices[0].message.content)")
    print()
    
    print("5. 预期响应格式")
    print("   所有端点会返回符合 OpenAI API 规范的 JSON 响应，包括:")
    print("   - id: 请求ID")
    print("   - object: 对象类型")  
    print("   - created: 时间戳")
    print("   - model: 模型名称")
    print("   - choices: 结果选择")
    print("   - usage: 用量统计")
    print()
    
    print("完成以上步骤后，您将验证API接口正常工作！")

if __name__ == "__main__":
    test_openai_compatible_apis()