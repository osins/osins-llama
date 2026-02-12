# CLI集成开发指南

## 概述

CLI（命令行界面）集成为用户提供了一个方便的方式来启动、管理和监控服务器。本指南详细描述了CLI的设计、实现和使用方式。

## CLI命令结构

### 主命令
- `llama` - 主命令
  - `start` - 启动服务器
  - `stop` - 停止服务器  
  - `restart` - 重启服务器
  - `status` - 查看服务器状态
  - `config` - 配置管理
  - `logs` - 日志查看
  - `health` - 健康检查

### 通用选项
- `--help` - 显示帮助信息
- `--verbose` - 详细输出
- `--config` - 指定配置文件路径

## start命令

### 功能
启动API服务器实例

### 参数
- `--model-path` - 模型文件路径
- `--host` - 服务器绑定地址 (默认: 0.0.0.0)
- `--port` - 服务器端口 (默认: 31301)
- `--n-ctx` - 上下文长度 (默认: 2048)
- `--n-threads` - 线程数 (默认: 8)
- `--api-keys` - API密钥列表 (逗号分隔)
- `--max-concurrent-requests` - 最大并发请求数 (默认: 10)
- `--rate-limit-requests` - 速率限制请求数 (默认: 60)
- `--rate-limit-window` - 速率限制时间窗口 (秒) (默认: 60)
- `--debug` - 调试模式 (默认: false)

### 示例
```bash
# 启动服务器
llama start --model-path ./models/model.gguf --port 31301

# 启动服务器并设置API密钥
llama start --model-path ./models/model.gguf --api-keys sk-123456,sk-789012

# 启动服务器并设置并发限制
llama start --model-path ./models/model.gguf --max-concurrent-requests 20
```

## stop命令

### 功能
停止正在运行的服务器实例

### 参数
- `--pid-file` - PID文件路径 (默认: ./llama.pid)
- `--force` - 强制停止 (默认: false)

### 示例
```bash
# 停止服务器
llama stop

# 指定PID文件停止服务器
llama stop --pid-file /tmp/llama.pid
```

## restart命令

### 功能
重启服务器实例

### 参数
- `--model-path` - 模型文件路径
- `--host` - 服务器绑定地址
- `--port` - 服务器端口
- `--wait` - 等待时间 (秒) (默认: 5)

### 示例
```bash
# 重启服务器
llama restart

# 重启服务器并等待更长时间
llama restart --wait 10
```

## status命令

### 功能
查看服务器运行状态

### 参数
- `--pid-file` - PID文件路径 (默认: ./llama.pid)
- `--api-url` - API端点URL (默认: http://localhost:31301)

### 示例
```bash
# 查看服务器状态
llama status

# 指定API端点查看状态
llama status --api-url http://myserver:31301
```

## config命令

### 功能
管理服务器配置

### 子命令
- `show` - 显示当前配置
- `set` - 设置配置项
- `reset` - 重置配置

### 示例
```bash
# 显示当前配置
llama config show

# 设置配置项
llama config set --n-ctx 4096
```

## logs命令

### 功能
查看服务器日志

### 参数
- `--follow` - 实时跟踪日志 (默认: false)
- `--lines` - 显示最后N行 (默认: 50)
- `--log-file` - 日志文件路径 (默认: ./llama.log)

### 示例
```bash
# 查看最后50行日志
llama logs

# 实时跟踪日志
llama logs --follow

# 查看最后100行日志
llama logs --lines 100
```

## health命令

### 功能
执行健康检查

### 参数
- `--api-url` - API端点URL (默认: http://localhost:31301)
- `--timeout` - 超时时间 (秒) (默认: 30)

### 示例
```bash
# 执行健康检查
llama health

# 指定API端点执行健康检查
llama health --api-url http://myserver:31301
```

## 实现要求

### 1. 命令解析
- 使用argparse或click进行参数解析
- 提供清晰的帮助信息
- 支持短参数和长参数

### 2. 配置管理
- 支持命令行参数
- 支持配置文件
- 支持环境变量
- 参数优先级: 命令行 > 配置文件 > 环境变量 > 默认值

### 3. 进程管理
- 启动时记录PID到文件
- 支持优雅关闭
- 支持进程监控
- 支持自动重启

### 4. 错误处理
- 提供清晰的错误信息
- 适当的退出码
- 异常情况处理
- 用户友好的提示

### 5. 日志管理
- 支持不同日志级别
- 日志文件轮转
- 结构化日志输出
- 日志检索功能

## 配置文件格式

### YAML格式
```yaml
server:
  host: "0.0.0.0"
  port: 31301
  debug: false

model:
  path: "./models/model.gguf"
  n_ctx: 2048
  n_threads: 8

security:
  api_keys: ["sk-123456", "sk-789012"]
  rate_limit_requests: 60
  rate_limit_window: 60

performance:
  max_concurrent_requests: 10
```

## 进程管理

### PID文件
- 默认路径: ./llama.pid
- 存储服务器进程ID
- 用于进程控制操作

### 信号处理
- SIGTERM: 优雅关闭
- SIGINT: 中断处理
- 信号处理函数实现

## 输出格式

### JSON输出 (可选)
- 支持JSON格式输出
- 便于脚本处理
- 使用--json参数启用

### 表格输出
- 状态信息表格显示
- 清晰的数据展示
- 颜色编码 (可选)

## 安全考虑

### 权限检查
- 检查文件访问权限
- 验证模型文件权限
- 防止权限提升

### 输入验证
- 验证路径参数
- 防止路径穿越
- 参数范围检查

### 敏感信息
- 不在命令行显示API密钥
- 安全的配置文件权限
- 日志中隐藏敏感信息

## 测试策略

### 单元测试
- 命令解析测试
- 参数验证测试
- 错误处理测试

### 集成测试
- 端到端命令测试
- 进程管理测试
- 配置加载测试

### 用户验收测试
- 手动命令测试
- 场景测试
- 边界条件测试

## 最佳实践

1. 提供清晰的帮助信息和文档
2. 实现一致的命令行接口
3. 提供丰富的配置选项
4. 实现可靠的进程管理
5. 提供详细的日志记录
6. 实现安全的参数处理
7. 提供错误恢复机制
8. 支持自动化脚本集成