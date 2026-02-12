# CLI 配置管理

## 配置文件格式

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
  api_keys_file: "/run/secrets/api_keys"  # 从安全文件加载API密钥
  rate_limit:
    enabled: true
    requests: 60
    window_seconds: 60
  enable_ip_limit: true

performance:
  max_concurrent_requests: 10
  request_timeout_seconds: 60

logging:
  level: INFO
  format: json
  access_log: true
  log_path: "/var/log/osins-llama/app.log"

tls:
  enabled: false
  cert_file: "/etc/certs/server.crt"
  key_file: "/etc/certs/server.key"

limits:
  max_request_size_mb: 10
  max_upload_workers: 4

audit:
  enabled: true
  log_path: "/var/log/osins-llama/audit.log"
```

### 配置优先级

配置项的优先级（从高到低）：

1. 命令行参数
2. 环境变量 (以LLAMA_为前缀)
3. 配置文件
4. 默认值

每层覆盖必须记录来源，最终合并结果可追踪。

## 环境变量

CLI支持通过环境变量设置配置项，所有环境变量都以`LLAMA_`为前缀：

- `LLAMA_SERVER_HOST`: 服务器主机地址
- `LLAMA_SERVER_PORT`: 服务器端口
- `LLAMA_MODEL_PATH`: 模型文件路径
- `LLAMA_SECURITY_API_KEYS_FILE`: API密钥文件路径
- `LLAMA_LOGGING_LEVEL`: 日志级别
- `LLAMA_PERFORMANCE_MAX_CONCURRENT_REQUESTS`: 最大并发请求数

API密钥必须通过环境变量或安全文件注入，不允许在配置文件中明文存储。

## 配置验证

所有配置项都会进行严格的验证：

### 服务器配置验证
- `server.host`: 合法IPv4/IPv6或域名，不允许URL格式、端口拼接、控制字符、空格；允许0.0.0.0和localhost
- `server.port`: 1024 ≤ port ≤ 65535（系统保留端口<1024需root权限）
- `server.debug`: 布尔值

### 模型配置验证
- `model.path`: 路径存在、是文件、可读权限、文件大小 > 0、扩展名必须为 .gguf
- `model.n_ctx`: 正整数，启动时解析模型metadata确定最大支持值，若metadata缺失或异常则启动失败；内存估算公式：n_ctx × 模型大小 × batch；硬限制 ≤ 32768
- `model.n_threads`: 1 ≤ n_threads ≤ CPU核数

### 安全配置验证
- `security.api_keys_file`: 文件存在、所有者为当前运行用户、非符号链接、权限600、非空、大小上限1MB、每行key非空且格式校验
- `security.rate_limit.enabled`: 布尔值，若false则忽略requests和window_seconds
- `security.rate_limit.requests`: ≥ 1，上限建议 <= 10000
- `security.rate_limit.window_seconds`: 1 ≤ window ≤ 3600
- `security.enable_ip_limit`: 布尔值

### 性能配置验证
- `performance.max_concurrent_requests`: ≥ 1，≤ (RLIMIT_NOFILE - 100) / 2（Linux）或系统经验上限（Windows）
- `performance.request_timeout_seconds`: 1 ≤ timeout ≤ 600

### 日志配置验证
- `logging.level`: DEBUG/INFO/WARNING/ERROR/CRITICAL之一
- `logging.format`: text/json之一
- `logging.access_log`: 布尔值
- `logging.log_path`: 禁止路径遍历、禁止符号链接、权限640或更严格、支持日志轮转

### TLS配置验证
- `tls.enabled`: 布尔值
- `tls.cert_file`: 文件存在、非符号链接、权限≤600、证书有效性校验
- `tls.key_file`: 文件存在、非符号链接、权限≤600、与cert匹配校验

### 限制配置验证
- `limits.max_request_size_mb`: 1 ≤ size ≤ 100
- `limits.max_upload_workers`: 0 ≤ workers ≤ CPU核数

### 审计配置验证
- `audit.enabled`: 布尔值
- `audit.log_path`: 禁止路径遍历、禁止符号链接、权限600、与业务日志路径分离

## 配置验证失败策略

- 启动阶段校验
- 聚合所有错误后一次性输出
- 错误信息包含字段路径
- 任一字段非法立即退出，退出码2
- 例如：
```
ConfigurationError:
 - server.port: must be between 1024 and 65535
 - model.path: file not found
```

## 字段说明表

| 字段 | 类型 | 默认值 | 范围 | 必填 | 安全级别 |
|------|------|--------|------|------|----------|
| server.host | str | "127.0.0.1" | 合法IP或域名 | 是 | 低 |
| server.port | int | 8000 | 1024-65535 | 是 | 低 |
| server.debug | bool | false | true/false | 否 | 低 |
| model.path | str | 无 | 存在且可读 | 是 | 低 |
| model.n_ctx | int | 2048 | ≥ 1, ≤ 32768 | 否 | 中 |
| model.n_threads | int | 8 | 1-CPU核数 | 否 | 中 |
| security.api_keys_file | str | 无 | 存在且权限600 | 否 | 高 |
| security.rate_limit.enabled | bool | true | true/false | 否 | 中 |
| security.rate_limit.requests | int | 60 | ≥ 1 | 否 | 中 |
| security.rate_limit.window_seconds | int | 60 | 1-3600 | 否 | 中 |
| security.enable_ip_limit | bool | true | true/false | 否 | 中 |
| performance.max_concurrent_requests | int | 10 | ≥ 1 | 否 | 中 |
| performance.request_timeout_seconds | int | 60 | 1-600 | 否 | 中 |
| logging.level | str | INFO | DEBUG/INFO/WARNING/ERROR/CRITICAL | 否 | 低 |
| logging.format | str | text | text/json | 否 | 低 |
| logging.access_log | bool | false | true/false | 否 | 低 |
| logging.log_path | str | ./app.log | 可写路径 | 否 | 低 |
| tls.enabled | bool | false | true/false | 否 | 高 |
| tls.cert_file | str | 无 | 存在且可读 | 否（启用时必填） | 高 |
| tls.key_file | str | 无 | 存在且可读 | 否（启用时必填） | 高 |
| limits.max_request_size_mb | int | 10 | 1-100 | 否 | 中 |
| limits.max_upload_workers | int | 4 | 0-CPU核数 | 否 | 中 |
| audit.enabled | bool | false | true/false | 否 | 高 |
| audit.log_path | str | ./audit.log | 可写路径 | 否 | 高 |

## 安全注意事项

- API密钥必须通过安全文件或环境变量注入
- 配置文件权限应设置为600
- 防止路径遍历攻击（..）
- 验证所有输入参数
- API Key在日志中必须做掩码处理（前4位 + ****）
- 禁止在debug模式输出配置全量
- 不允许在异常栈中打印密钥内容
- 日志必须支持脱敏策略
- 启用速率限制必须线程安全，生产环境使用Redis等集中式存储
- 配置文件支持hash校验和immutable模式
- TLS证书必须校验有效性、权限和匹配性
- audit日志与业务日志路径分离
- debug=true且host=0.0.0.0时打印强警告

## 启动自检

- 模型加载测试
- 线程池创建测试
- 限流初始化测试
- API Key文件读取测试
- 端口可用性检查
- 内存可用性检查
- 磁盘空间检查
- TLS证书加载测试（若启用）
- Redis连接测试（若限流启用）
- 文件描述符限制检查
- CPU核数检查
- 模型metadata解析验证
- 日志路径可写性验证
- audit日志路径可写性验证