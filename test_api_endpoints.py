"""
验证OpenAI API接口可用性
"""
import requests
import time
import threading
import subprocess
from pathlib import Path
import sys


def test_api_endpoints(port=31301):
    """
    测试API端点的可用性
    """
    base_url = f"http://127.0.0.1:{port}"
    
    print(f"正在测试 API 端点 @ {base_url}")
    
    # 定义所有端点
    endpoints = [
        ("/", "GET", "服务健康检查"),
        ("/health", "GET", "健康状态"),
        ("/v1/models", "GET", "模型列表"),
        ("/v1/chat/completions", "POST", "聊天补全"),
        ("/v1/completions", "POST", "文本补全"),
        ("/v1/embeddings", "POST", "嵌入向量")
    ]
    
    # 测试每个端点
    for path, method, description in endpoints:
        try:
            url = f"{base_url}{path}"
            print(f"\n--- 测试: {description} ({method} {path}) ---")
            
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                # 准备请求体
                if path == "/v1/chat/completions":
                    data = {
                        "model": "test-model",
                        "messages": [{"role": "user", "content": "Hello"}],
                        "temperature": 0.5,
                        "max_tokens": 10
                    }
                elif path == "/v1/completions":
                    data = {
                        "model": "test-model", 
                        "prompt": "Hello world",
                        "temperature": 0.5,
                        "max_tokens": 10
                    }
                elif path == "/v1/embeddings":
                    data = {
                        "model": "test-model",
                        "input": "Hello world"
                    }
                else:
                    data = {}
                    
                response = requests.post(url, json=data, timeout=10)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ 端点工作正常")
                try:
                    json_resp = response.json()
                    print(f"响应: {json_resp}")
                except:
                    print(f"响应: {response.text[:200]}...")
            elif response.status_code == 404:
                print("⚠ 端点不存在 (404)")
            elif response.status_code == 405:
                print("⚠ 方法不允许 (405)")
            else:
                print(f"✗ 状态码 {response.status_code}")
                try:
                    print(f"错误: {response.json()}")
                except:
                    print(f"错误: {response.text[:200]}...")
                    
        except requests.exceptions.ConnectionError:
            print(f"✗ 连接失败 - 服务可能未启动")
        except requests.exceptions.Timeout:
            print(f"✗ 请求超时")
        except Exception as e:
            print(f"✗ 请求失败: {str(e)}")


def start_test_server():
    """
    启动测试服务器
    """
    print("此脚本仅演示API接口测试流程")
    print("---")
    print("API端点功能概览:")
    print("1. GET /v1/models - 返回可用模型列表")
    print("2. POST /v1/chat/completions - OpenAI聊天接口兼容")
    print("3. POST /v1/completions - OpenAI文本补全兼容")
    print("4. POST /v1/embeddings - 向量嵌入接口")
    
    print("\n使用方法:")
    print("$ llama start -m /path/to/model.gguf --port 31301")
    print("# 然后在另一个终端运行测试")
    print("curl http://127.0.0.1:31301/v1/models")
    
    print("\nAPI兼容格式:")
    # 演示实际可用的请求格式
    print('\ncurl -X POST http://127.0.0.1:31301/v1/chat/completions \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"model":"test","messages":[{"role":"user","content":"Hi"}],"temperature":0.7,"max_tokens":50}\'')
    
    
if __name__ == "__main__":
    print("=== OpenAI API 接口可用性验证 ===")
    
    # 如果有参数传入，测试特定端口，否则只运行演示
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        test_api_endpoints(port)
    else:
        start_test_server()