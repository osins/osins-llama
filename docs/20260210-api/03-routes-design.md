# 路由设计

## 路由分类
每个路由功能将放在独立的文件中，便于管理和维护。

## 路由列表
1. `completion_routes.py` - 处理 /v1/completions 端点
2. `chat_routes.py` - 处理 /v1/chat/completions 端点

## 端点规范
- `/v1/completions` - OpenAI 兼容的文本生成端点
- `/v1/chat/completions` - OpenAI 兼容的聊天生成端点

## 实现要点
- 正确处理AI模型参数映射
- 实现错误处理机制
- 集成 llama-cpp-python AI模型
- 计算和返回使用量统计