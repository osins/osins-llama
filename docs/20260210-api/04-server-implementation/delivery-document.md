# 服务器实现交付文档

## 项目概述

本项目实现了基于 llama-cpp-python 的生产级推理 API 服务，兼容 OpenAI Chat/Completion 接口风格。系统具备高并发、可观测、安全、可测试、可扩展的特性。

## 功能清单

### 核心功能
1. **API 服务** - 兼容 OpenAI 接口的补全和聊天 API
2. **模型管理** - 支持模型的加载、卸载和管理
3. **并发控制** - 限制最大并发请求数，保护模型资源
4. **流式响应** - 支持同步和流式两种响应方式
5. **Token 统计** - 准确计算输入输出 Token 数量
6. **健康检查** - 提供服务状态监控端点

### 安全功能
1. **身份验证** - 支持 Bearer Token 认证
2. **速率限制** - 基于 IP 或用户的请求频率限制
3. **参数校验** - 严格的输入参数验证
4. **访问控制** - 限制模型加载路径，防止路径穿越

### 监控功能
1. **结构化日志** - 详细的请求和响应日志
2. **性能指标** - 响应时间和吞吐量统计
3. **健康状态** - 实时服务健康状况检查

## 技术架构

### 目录结构
```
src/
server/
app.py          # FastAPI 应用初始化
config.py       # 配置管理
dependency.py   # 依赖注入
lifecycle.py    # 应用生命周期管理

api/
routes/
health.py       # 健康检查路由
completion.py   # 补全 API 路由
chat.py         # 聊天 API 路由
models.py       # API 数据模型

services/
inference_service.py  # 推理服务
model_manager.py      # 模型管理器
scheduler.py          # 请求调度器
token_service.py      # Token 服务

core/
llama_wrapper.py      # llama-cpp 封装
stream_generator.py   # 流式生成器
error_codes.py        # 错误码定义

schemas/
completion_request.py   # 补全请求模型
completion_response.py  # 补全响应模型
chat_request.py         # 聊天请求模型
chat_response.py        # 聊天响应模型
usage.py              # 使用量模型
error_response.py     # 错误响应模型

middleware/
auth_middleware.py        # 认证中间件
logging_middleware.py     # 日志中间件
rate_limit_middleware.py  # 限流中间件

utils/
token_utils.py    # Token 工具函数
id_generator.py   # ID 生成器
```

### API 端点

#### 健康检查
- `GET /v1/health` - 检查服务状态

#### 模型管理
- `GET /v1/models` - 列出可用模型

#### 补全 API
- `POST /v1/completions` - 文本补全，支持流式和非流式响应

#### 聊天 API
- `POST /v1/chat/completions` - 聊天补全，支持流式和非流式响应

### 配置参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| LLAMA_MODEL_PATH | 模型文件路径 | - |
| LLAMA_N_CTX | 上下文长度 | 2048 |
| LLAMA_N_THREADS | 线程数 | 8 |
| LLAMA_VERBOSE | 详细日志 | false |
| LLAMA_MAX_PROMPT_TOKENS | 最大提示 Token 数 | 2048 |
| LLAMA_MAX_TOTAL_TOKENS | 最大总 Token 数 | 4096 |
| LLAMA_MAX_BATCH_SIZE | 最大批处理大小 | 1 |
| LLAMA_API_KEYS | API 密钥列表 | [] |
| LLAMA_RATE_LIMIT_REQUESTS | 限流请求数 | 60 |
| LLAMA_RATE_LIMIT_WINDOW | 限流窗口（秒） | 60 |
| LLAMA_MAX_CONCURRENT_REQUESTS | 最大并发请求数 | 10 |
| LLAMA_HOST | 服务主机 | 0.0.0.0 |
| LLAMA_PORT | 服务端口 | 31301 |
| LLAMA_DEBUG | 调试模式 | false |

## 部署说明

### 环境要求
- Python 3.8+
- llama-cpp-python
- FastAPI
- Uvicorn

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行服务
```bash
# 使用命令行
python -m src.server.app

# 或使用 uvicorn
uvicorn src.server.app:app --host 0.0.0.0 --port 31301
```

### 生产部署
```bash
# 使用 gunicorn
gunicorn src.server.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:31301
```

## 测试验证

### 单元测试
```bash
pytest tests/unit/
```

### 集成测试
```bash
pytest tests/integration/
```

### API 测试
```bash
# 测试补全 API
curl -X POST http://localhost:31301/v1/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "test-model",
    "prompt": "Hello, world!",
    "max_tokens": 100
  }'

# 测试聊天 API
curl -X POST http://localhost:31301/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "test-model",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100
  }'
```

## 安全说明

1. **API 密钥保护** - 建议使用强密钥并定期轮换
2. **网络访问控制** - 通过反向代理限制访问
3. **输入验证** - 所有输入参数都会进行严格验证
4. **模型路径限制** - 仅允许从预设目录加载模型

## 监控和运维

### 日志
- 结构化日志输出到标准输出
- 记录请求 ID、响应时间、Token 用量等信息

### 健康检查
- `/v1/health` 端点提供服务状态信息
- 返回模型加载状态和队列长度

### 性能调优
- 根据硬件资源调整 `LLAMA_N_THREADS`
- 根据负载调整 `LLAMA_MAX_CONCURRENT_REQUESTS`
- 合理设置 `LLAMA_N_CTX` 以平衡内存使用和性能

## 依赖关系

- llama-cpp-python: 模型推理引擎
- FastAPI: Web 框架
- Pydantic: 数据校验
- Uvicorn: ASGI 服务器
- psutil: 系统和进程监控
- requests: HTTP 客户端

## 故障排除

1. **模型加载失败** - 检查模型文件路径和权限
2. **内存不足** - 调整上下文大小和批处理大小
3. **API 访问被拒绝** - 检查 API 密钥配置
4. **并发限制** - 调整并发请求数配置

## 扩展建议

1. **多模型支持** - 扩展模型管理器以支持多个模型实例
2. **分布式部署** - 使用 Redis 实现分布式限流和缓存
3. **缓存机制** - 添加响应缓存以提升性能
4. **计费系统** - 集成 Token 使用量计费功能