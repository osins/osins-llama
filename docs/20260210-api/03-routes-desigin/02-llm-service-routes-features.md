# LLM 服务路由设计功能清单

## 1. Routes 层

| 文件路径 | 功能描述 |
|----------|---------|
| `src/llama/api/completion_routes.py` | `/v1/completions` 路由，参数校验、API Key 验证、流式/非流式响应、异常处理 |
| `src/llama/api/chat_routes.py` | `/v1/chat/completions` 路由，参数校验、API Key 验证、流式/非流式响应、异常处理 |

## 2. Service 层

| 文件路径 | 功能描述 |
|----------|---------|
| `src/llama/services/completion_service.py` | 调用 ModelManager.generate()，token 限制、流式处理、OpenAI JSON 格式化、异常转换 |
| `src/llama/services/chat_service.py` | 调用 ModelManager.generate()，多轮对话 token 检查、流式处理、OpenAI JSON 格式化、异常转换 |

## 3. 核心模型管理

| 文件路径 | 功能描述 |
|----------|---------|
| `src/llama/core/model_manager.py` | 单一模型实例、并发控制（Semaphore）、请求排队、超时控制、generate() 接口 |

## 4. 配置文件

| 文件路径 | 功能描述 |
|----------|---------|
| `src/llama/config/config.yaml` | 模型参数、并发/排队/超时、API Key、限流、流式控制、日志、部署参数 |

## 5. 启动入口

| 文件路径 | 功能描述 |
|----------|---------|
| `src/llama/main.py` | 读取配置、初始化 ModelManager、注册 routes、启动 FastAPI + Uvicorn |

## 6. 辅助工具（可选）

| 文件路径 | 功能描述 |
|----------|---------|
| `src/llama/utils/token_utils.py` | 计算 token 数量、检查超限 |
| `src/llama/utils/response_formatter.py` | 模型输出格式化为 OpenAI 兼容 JSON |
| `src/llama/utils/security.py` | API Key 验证、限流逻辑 |
