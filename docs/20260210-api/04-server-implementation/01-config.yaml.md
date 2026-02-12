# 服务器配置文件规范

## 配置文件结构

服务器使用环境变量进行配置，所有配置项均以 `LLAMA_` 为前缀。

## 核心配置项

### 模型配置 (ModelConfig)
- `LLAMA_MODEL_PATH` - 模型文件路径（必需）
- `LLAMA_N_CTX` - 上下文长度，默认 2048
- `LLAMA_N_THREADS` - 线程数，默认 8
- `LLAMA_VERBOSE` - 详细日志模式，默认 false

### 资源配置 (ResourcesConfig)
- `LLAMA_MAX_PROMPT_TOKENS` - 最大提示 Token 数，默认 2048
- `LLAMA_MAX_TOTAL_TOKENS` - 最大总 Token 数，默认 4096
- `LLAMA_MAX_BATCH_SIZE` - 最大批处理大小，默认 1

### 安全配置 (SecurityConfig)
- `LLAMA_API_KEYS` - API 密钥列表，逗号分隔
- `LLAMA_RATE_LIMIT_REQUESTS` - 速率限制请求数，默认 60
- `LLAMA_RATE_LIMIT_WINDOW` - 速率限制时间窗口（秒），默认 60
- `LLAMA_MAX_CONCURRENT_REQUESTS` - 最大并发请求数，默认 10

### 服务配置 (ServiceConfig)
- `LLAMA_HOST` - 服务监听地址，默认 0.0.0.0
- `LLAMA_PORT` - 服务端口，默认 31301
- `LLAMA_DEBUG` - 调试模式，默认 false

## 配置加载顺序

1. 默认值
2. 环境变量
3. 配置文件（如果有）

## 配置验证

所有配置项都会进行类型验证和范围检查：
- 端口号必须在 1-65535 范围内
- 线程数必须为正整数
- 上下文长度不能超过限制
- API 密钥不能为空

## 配置示例

### 开发环境
```bash
LLAMA_MODEL_PATH=./models/llama-2-7b-chat.Q4_K_M.gguf
LLAMA_N_CTX=2048
LLAMA_N_THREADS=4
LLAMA_API_KEYS=sk-fakekey123
LLAMA_DEBUG=true
```

### 生产环境
```bash
LLAMA_MODEL_PATH=/opt/models/llama-2-7b-chat.Q4_K_M.gguf
LLAMA_N_CTX=4096
LLAMA_N_THREADS=16
LLAMA_API_KEYS=sk-prodkey123,sk-prodkey456
LLAMA_RATE_LIMIT_REQUESTS=100
LLAMA_MAX_CONCURRENT_REQUESTS=20
LLAMA_DEBUG=false
```

## 安全注意事项

- 敏感配置项（如 API 密钥）不应硬编码在代码中
- 使用环境变量或配置管理系统管理敏感配置
- 定期轮换 API 密钥
- 限制对配置文件的访问权限

## 动态配置

某些配置项可以在运行时动态调整：
- 速率限制参数
- 日志级别
- 调试标志

## 配置文件位置

- 主配置文件：`config/settings.yaml`（可选）
- 环境配置文件：`.env`
- Docker 环境：通过 `-e` 参数传入

## 配置迁移

- 从旧版本迁移时，确保配置项名称和格式兼容
- 使用配置验证确保新配置的正确性
- 在更改配置后重启服务