# 命令行启动 osins-llama 服务指南

## 基本命令格式

使用以下命令启动 osins-llama 服务：

```bash
# 方式1：通过模块执行
python -m src.llama.cli.main start [OPTIONS]

# 方式2：直接执行脚本
python src/llama/cli/main.py start [OPTIONS]
```

## 必要参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--model-path` | **必填**，指定模型文件路径 | `--model-path /path/to/model.gguf` |

## 常用可选参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--host` | 服务器绑定地址 | `127.0.0.1` | `--host 0.0.0.0` |
| `--port` | 服务器端口（1024-65535） | `31301` | `--port 8000` |
| `--n-ctx` | 上下文长度（128-32768） | `2048` | `--n-ctx 4096` |
| `--n-threads` | 线程数（1-64） | 自动检测（最大8或CPU核心数） | `--n-threads 4` |
| `--api-keys` | API密钥列表（逗号分隔） | 无 | `--api-keys key1,key2` |
| `--max-concurrent-requests` | 最大并发请求数（1-100） | `10` | `--max-concurrent-requests 20` |
| `--debug` | 启用调试模式（生产环境禁用） | `False` | `--debug` |
| `--pid-file` | PID文件路径 | `./llama.pid` | `--pid-file /tmp/llama.pid` |
| `--config` | 指定配置文件路径 | 无 | `--config /etc/osins-llama/config.json` |
| `--verbose` | 启用详细输出 | `False` | `--verbose` |

## 启动示例

### 基本启动（使用默认配置）
```bash
python -m src.llama.cli.main start --model-path /path/to/model.gguf
```

### 自定义配置启动
```bash
python -m src.llama.cli.main start \
  --model-path /path/to/model.gguf \
  --host 0.0.0.0 \
  --port 8000 \
  --n-ctx 4096 \
  --n-threads 8 \
  --api-keys key1,key2 \
  --max-concurrent-requests 20
```

### 使用配置文件启动
```bash
python -m src.llama.cli.main start \
  --model-path /path/to/model.gguf \
  --config /etc/osins-llama/config.json \
  --verbose
```

## 其他相关命令

### 停止服务
```bash
python -m src.llama.cli.main stop
```

### 重启服务
```bash
python -m src.llama.cli.main restart --model-path /path/to/model.gguf
```

### 查看服务状态
```bash
python -m src.llama.cli.main status
```

### 检查服务健康状态
```bash
python -m src.llama.cli.main health
```

### 查看日志
```bash
python -m src.llama.cli.main logs
```

### 查看配置信息
```bash
python -m src.llama.cli.main config
```

## 注意事项

1. **安全性**：生产环境建议：
   - 使用 `--host 127.0.0.1` 或内网IP，避免公网直接访问
   - 配置 `--api-keys` 进行访问控制
   - 禁用 `--debug` 模式

2. **性能优化**：
   - `--n-threads` 建议设置为CPU核心数
   - `--n-ctx` 根据模型能力和内存情况调整
   - 合理设置 `--max-concurrent-requests` 避免系统过载

3. **模型文件**：
   - 确保模型文件路径正确且有读取权限
   - 模型文件必须是常规文件，不能是符号链接
   - 模型文件大小默认限制为10GB，可通过 `MAX_MODEL_SIZE` 环境变量调整

4. **PID文件**：
   - PID文件用于管理服务进程
   - 启动前会检查PID文件是否存在，避免重复启动
   - 启动失败时会自动清理PID文件

## 完整命令帮助

查看完整的命令帮助：

```bash
python -m src.llama.cli.main start --help
```