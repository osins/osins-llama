# 服务器实现快速参考

## 项目结构
```
src/
├── server/
│   ├── app.py           # FastAPI 应用入口
│   ├── config.py        # 配置管理
│   ├── dependency.py    # 依赖注入
│   └── lifecycle.py     # 生命周期管理
├── api/
│   ├── routes/
│   │   ├── health.py    # 健康检查
│   │   ├── completion.py # 补全 API
│   │   └── chat.py      # 聊天 API
│   └── models.py        # API 模型
├── services/
│   ├── inference_service.py # 推理服务
│   ├── model_manager.py     # 模型管理
│   ├── scheduler.py         # 调度器
│   └── token_service.py     # Token 服务
├── core/
│   ├── llama_wrapper.py     # llama-cpp 封装
│   ├── stream_generator.py  # 流式生成器
│   └── error_codes.py       # 错误码
├── schemas/
│   ├── completion_request.py  # 补全请求
│   ├── completion_response.py # 补全响应
│   ├── chat_request.py        # 聊天请求
│   ├── chat_response.py       # 聊天响应
│   ├── usage.py              # 用量模型
│   └── error_response.py     # 错误响应
├── middleware/
│   ├── auth_middleware.py        # 认证中间件
│   ├── logging_middleware.py     # 日志中间件
│   └── rate_limit_middleware.py  # 限流中间件
└── utils/
    ├── token_utils.py  # Token 工具
    └── id_generator.py # ID 生成器
```

## 主要配置项
- `LLAMA_MODEL_PATH` - 模型路径
- `LLAMA_N_CTX` - 上下文长度
- `LLAMA_N_THREADS` - 线程数
- `LLAMA_API_KEYS` - API 密钥列表
- `LLAMA_RATE_LIMIT_REQUESTS` - 限流请求数
- `LLAMA_MAX_CONCURRENT_REQUESTS` - 最大并发数

## 常用命令
```bash
# 启动服务
python -m src.server.app

# 运行测试
pytest tests/

# 检查类型
mypy src/

# 格式化代码
black src/
```

## API 端点
- `GET /v1/health` - 健康检查
- `GET /v1/models` - 模型列表
- `POST /v1/completions` - 补全 API
- `POST /v1/chat/completions` - 聊天 API

## 错误码
- `MODEL_NOT_FOUND` - 模型未找到
- `INVALID_REQUEST` - 请求无效
- `CONTEXT_OVERFLOW` - 上下文溢出
- `RATE_LIMIT_EXCEEDED` - 速率限制超限
- `AUTH_FAILED` - 认证失败
- `INTERNAL_ERROR` - 内部错误

## 环境变量
```bash
export LLAMA_MODEL_PATH=/path/to/model.gguf
export LLAMA_API_KEYS=sk-123456,sk-789012
export LLAMA_RATE_LIMIT_REQUESTS=100
export LLAMA_MAX_CONCURRENT_REQUESTS=10
```

## 常见问题排查
1. 模型加载失败 - 检查路径和权限
2. 内存不足 - 调整 n_ctx 参数
3. API 访问被拒 - 检查 API 密钥配置
4. 并发限制 - 调整最大并发数配置

## 性能调优
- 调整 n_threads 以匹配 CPU 核心数
- 根据内存调整 n_ctx
- 设置合适的并发限制
- 使用 SSD 存储模型文件

## 安全要点
- 使用强 API 密钥
- 限制模型文件目录访问
- 配置反向代理进行额外保护
- 定期轮换 API 密钥