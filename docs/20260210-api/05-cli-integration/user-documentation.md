# CLI 使用文档

## 概述

CLI（命令行界面）为用户提供了一个方便的方式来启动、管理和监控osins-llama服务器。本文档详细介绍了CLI的安装、配置和使用方法。

## 安装

CLI工具随osins-llama包一起安装：

```bash
pip install osins-llama
```

安装完成后，您可以使用`llama`命令来管理服务器。

## 基本用法

### 帮助信息

获取CLI工具的帮助信息：

```bash
llama --help
```

获取特定命令的帮助信息：

```bash
llama start --help
llama stop --help
llama status --help
```

### 通用选项

- `--verbose`: 启用详细输出
- `--config PATH`: 指定配置文件路径

## 命令详解

### start - 启动服务器

启动osins-llama服务器实例。

#### 语法

```bash
llama start [OPTIONS]
```

#### 选项

- `--model-path PATH`: 模型文件路径
- `--host TEXT`: 服务器绑定地址 (默认: 0.0.0.0)
- `--port INTEGER`: 服务器端口 (默认: 31301)
- `--n-ctx INTEGER`: 上下文长度 (默认: 2048)
- `--n-threads INTEGER`: 线程数 (默认: 8)
- `--api-keys TEXT`: API密钥列表 (逗号分隔)
- `--max-concurrent-requests INTEGER`: 最大并发请求数 (默认: 10)
- `--rate-limit-requests INTEGER`: 速率限制请求数 (默认: 60)
- `--rate-limit-window INTEGER`: 速率限制时间窗口 (秒) (默认: 60)
- `--debug / --no-debug`: 调试模式 (默认: false)
- `--pid-file PATH`: PID文件路径 (默认: ./llama.pid)

#### 示例

```bash
# 启动服务器
llama start --model-path ./models/model.gguf --port 31301

# 启动服务器并设置API密钥
llama start --model-path ./models/model.gguf --api-keys sk-123456,sk-789012

# 启动服务器并设置并发限制
llama start --model-path ./models/model.gguf --max-concurrent-requests 20
```

### stop - 停止服务器

停止正在运行的服务器实例。

#### 语法

```bash
llama stop [OPTIONS]
```

#### 选项

- `--pid-file PATH`: PID文件路径 (默认: ./llama.pid)
- `--force`: 强制停止 (默认: false)

#### 示例

```bash
# 停止服务器
llama stop

# 指定PID文件停止服务器
llama stop --pid-file /tmp/llama.pid

# 强制停止服务器
llama stop --force
```

### restart - 重启服务器

重启服务器实例。

#### 语法

```bash
llama restart [OPTIONS]
```

#### 选项

- `--model-path PATH`: 模型文件路径
- `--host TEXT`: 服务器绑定地址
- `--port INTEGER`: 服务器端口
- `--wait INTEGER`: 等待时间 (秒) (默认: 5)
- `--pid-file PATH`: PID文件路径 (默认: ./llama.pid)

#### 示例

```bash
# 重启服务器
llama restart

# 重启服务器并等待更长时间
llama restart --wait 10
```

### status - 查看服务器状态

查看服务器运行状态。

#### 语法

```bash
llama status [OPTIONS]
```

#### 选项

- `--pid-file PATH`: PID文件路径 (默认: ./llama.pid)
- `--api-url TEXT`: API端点URL (默认: http://localhost:31301)

#### 示例

```bash
# 查看服务器状态
llama status

# 指定API端点查看状态
llama status --api-url http://myserver:31301
```

### config - 配置管理

管理服务器配置。

#### 语法

```bash
llama config COMMAND [OPTIONS]
```

#### 子命令

- `show`: 显示当前配置
- `set KEY VALUE`: 设置配置项
- `reset`: 重置配置

#### 示例

```bash
# 显示当前配置
llama config show

# 设置配置项
llama config set --n-ctx 4096
```

### logs - 查看服务器日志

查看服务器日志。

#### 语法

```bash
llama logs [OPTIONS]
```

#### 选项

- `--follow`: 实时跟踪日志 (默认: false)
- `--lines INTEGER`: 显示最后N行 (默认: 50)
- `--log-file PATH`: 日志文件路径 (默认: ./llama.log)

#### 示例

```bash
# 查看最后50行日志
llama logs

# 实时跟踪日志
llama logs --follow

# 查看最后100行日志
llama logs --lines 100
```

### health - 健康检查

执行健康检查。

#### 语法

```bash
llama health [OPTIONS]
```

#### 选项

- `--api-url TEXT`: API端点URL (默认: http://localhost:31301)
- `--timeout INTEGER`: 超时时间 (秒) (默认: 30)

#### 示例

```bash
# 执行健康检查
llama health

# 指定API端点执行健康检查
llama health --api-url http://myserver:31301
```

## 配置文件

CLI支持使用YAML格式的配置文件来管理服务器设置。

### 配置文件格式

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

### 配置优先级

配置项的优先级（从高到低）：

1. 命令行参数
2. 环境变量 (以LLAMA_为前缀)
3. 配置文件
4. 默认值

## 环境变量

CLI支持通过环境变量设置配置项，所有环境变量都以`LLAMA_`为前缀：

- `LLAMA_HOST`: 服务器主机地址
- `LLAMA_PORT`: 服务器端口
- `LLAMA_MODEL_PATH`: 模型文件路径
- `LLAMA_API_KEYS`: API密钥列表
- `LLAMA_LOG_LEVEL`: 日志级别

## PID文件管理

CLI使用PID文件来跟踪服务器进程：

- 默认位置：`./llama.pid`
- 存储服务器进程ID
- 用于进程控制操作
- 服务器停止时自动删除

## 日志管理

CLI支持日志记录：

- 默认位置：`./llama.log`
- 支持日志轮转
- 支持JSON格式输出
- 敏感信息会被脱敏处理

## 安全考虑

### PID文件安全

- 防止符号链接攻击
- 验证PID文件权限
- 验证进程归属

### 敏感信息保护

- API密钥不会在命令行或日志中明文显示
- 配置文件应设置适当的权限
- 日志中的敏感信息会被脱敏

## 故障排除

### 常见问题

1. **服务器无法启动**
   - 检查模型文件路径是否正确
   - 检查端口是否已被占用
   - 查看日志文件获取详细错误信息

2. **无法停止服务器**
   - 检查PID文件是否存在
   - 检查PID文件中的进程ID是否有效
   - 尝试使用`--force`选项强制停止

3. **配置文件加载失败**
   - 检查YAML语法是否正确
   - 检查文件路径是否有效
   - 确认文件权限是否合适

### 退出码

- `0`: 成功
- `1`: 一般错误
- `2`: 参数错误
- `3`: 权限问题
- `4`: 超时

## 高级用法

### 脚本集成

CLI工具设计为支持脚本集成：

```bash
#!/bin/bash

# 启动服务器并等待
llama start --model-path ./model.gguf --port 31301
sleep 5

# 检查状态
if llama status; then
    echo "Server is running"
else
    echo "Server failed to start"
    exit 1
fi

# 执行一些操作
# ...

# 停止服务器
llama stop
```

### 监控集成

使用`status`和`health`命令集成到监控系统中：

```bash
# 检查服务器状态
llama status && echo "OK" || echo "FAIL"

# 执行健康检查
llama health && echo "Healthy" || echo "Unhealthy"
```