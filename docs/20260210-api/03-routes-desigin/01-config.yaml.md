# config.yaml - 生产级可配置项

model:
  path: "models/xxx.gguf"        # 权重文件路径
  n_ctx: 4096                     # 上下文窗口
  n_gpu_layers: 32                # 使用 GPU 层数
  n_batch: 8                      # 批量推理大小
  n_threads: 4                    # CPU 线程数（fallback）
  quantization: "Q4_K_M"          # 量化类型，可选 Q4_K_M、Q8_0 等

resources:
  max_concurrent_requests: 1      # 最大同时推理请求数（Semaphore）
  max_queue_size: 16              # 等待队列长度
  request_timeout_seconds: 60     # 单请求最大超时
  max_prompt_tokens: 2048         # 最大 prompt token
  max_generation_tokens: 1024     # 最大生成 token
  max_total_tokens: 3072          # prompt + generation 总和

api:
  enable_stream: true             # 是否允许流式返回
  require_api_key: true           # 是否启用 API Key 验证
  api_keys:                        # 可使用多个 Key
    - "your_api_key_1"
    - "your_api_key_2"
  max_request_body_size: 1048576  # 请求体大小限制，字节

logging:
  log_level: "INFO"               # DEBUG / INFO / WARN / ERROR
  enable_prompt_logging: false    # 是否记录完整 prompt
  log_file: "logs/server.log"     # 日志文件路径

security:
  rate_limit_rps: 5               # 每秒请求数
  rate_limit_rpm: 300             # 每分钟请求数

storage:                           # 存储配置，用于分布式环境
  redis_host: "localhost"         # Redis 主机地址
  redis_port: 6379                # Redis 端口
  redis_db: 0                     # Redis 数据库索引
  redis_password: ""              # Redis 密码（可选）

deployment:
  host: "0.0.0.0"
  port: 8000
  workers: 1                      # Uvicorn worker 数
  reload: false                    # 开发模式热重载

advanced:
  seed: null                       # 随机种子，可选
  logprobs: false                  # 是否返回 token 概率
  function_call: false              # 是否支持 function_call
  tool_calls: false                 # 是否支持工具调用
