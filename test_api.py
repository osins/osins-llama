import time
import requests
import sys

def test_api():
    print("Testing API connection...")
    
    # 测试基本连接
    for attempt in range(30):  # 30秒超时
        try:
            print(f"Attempt {attempt + 1}: Trying to connect to server...")
            
            # 首先测试根URL
            response = requests.get("http://localhost:31301/", timeout=5)
            print(f"Base URL Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Server is responding!")
                
                # 测试带API密钥的健康检查
                headers = {
                    "Authorization": "Bearer sk-test123"
                }
                health_response = requests.get("http://localhost:31301/health", headers=headers, timeout=5)
                print(f"Health check Status: {health_response.status_code}")
                
                # 测试聊天API
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer sk-test123"
                }
                
                payload = {
                    "model": "test",
                    "messages": [
                        {"role": "user", "content": "你好"}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 100
                }
                
                chat_response = requests.post(
                    "http://localhost:31301/v1/chat/completions", 
                    headers=headers, 
                    json=payload, 
                    timeout=30
                )
                
                print(f"Chat API Status: {chat_response.status_code}")
                
                if chat_response.status_code == 200:
                    print("✓ Chat API working correctly")
                    print(f"Response: {chat_response.json()}")
                else:
                    print(f"✗ Chat API not ready, status: {chat_response.status_code}")
                
                return True
            else:
                print(f"Server returned {response.status_code}, retrying in 5 seconds...")
                
        except requests.exceptions.ConnectionError:
            print("Connection failed, server may still be starting up. Retrying...")
        except requests.exceptions.Timeout:
            print("Request timed out, retrying...")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(5)  # 等待 5 秒后重试
        
    print("Failed to connect to server within timeout period")
    return False

if __name__ == "__main__":
    test_api()