import http.client
import json

# 创建到本地服务器的连接
conn = http.client.HTTPConnection("localhost", 31301)

try:
    # 发送GET请求到根路径
    conn.request("GET", "/")
    
    # 获取响应
    response = conn.getresponse()
    
    print(f"Status: {response.status}")
    print(f"Reason: {response.reason}")
    
    # 读取响应数据
    data = response.read()
    print(f"Response data: {data.decode('utf-8')}")
    
    # 尝试解析为JSON（如果有的话）
    try:
        json_data = json.loads(data.decode('utf-8'))
        print(f"JSON response: {json_data}")
    except:
        print("Response is not JSON format")
        
finally:
    conn.close()