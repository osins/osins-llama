# 服务器部署和运维规范

## 部署概述

服务器部署规范涵盖了从开发到生产环境的完整部署流程，包括环境准备、配置管理、部署策略、监控运维等方面。

## 环境要求

### 硬件要求
- CPU: 至少4核心，推荐8核心以上
- 内存: 至少16GB RAM，根据模型大小调整
- 存储: SSD存储，至少50GB可用空间
- GPU: (可选) NVIDIA GPU支持CUDA (如需要GPU加速)

### 软件要求
- Python 3.8+ (推荐3.10或更高版本)
- pip包管理器
- Git (用于版本控制)
- Docker (可选，用于容器化部署)

### 系统依赖
- llama-cpp-python (依赖于C++编译工具链)
- BLAS/LAPACK库 (用于数学计算加速)

## 部署方式

### 1. 直接部署

#### 环境准备
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 服务启动
```bash
# 使用uvicorn直接启动
uvicorn src.server.app:app --host 0.0.0.0 --port 31301

# 或使用gunicorn (生产环境推荐)
gunicorn src.server.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:31301
```

### 2. 容器化部署

#### Dockerfile示例
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 31301

CMD ["gunicorn", "src.server.app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:31301"]
```

#### Docker Compose示例
```yaml
version: '3.8'

services:
  llama-api:
    build: .
    ports:
      - "31301:31301"
    environment:
      - LLAMA_MODEL_PATH=/models/model.gguf
      - LLAMA_N_CTX=4096
      - LLAMA_N_THREADS=8
      - LLAMA_API_KEYS=sk-123456,sk-789012
    volumes:
      - ./models:/models
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G
```

### 3. Kubernetes部署

#### Deployment配置
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llama-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llama-api
  template:
    metadata:
      labels:
        app: llama-api
    spec:
      containers:
      - name: llama-api
        image: llama-api:latest
        ports:
        - containerPort: 31301
        env:
        - name: LLAMA_MODEL_PATH
          value: "/models/model.gguf"
        - name: LLAMA_N_CTX
          value: "4096"
        - name: LLAMA_N_THREADS
          value: "8"
        - name: LLAMA_API_KEYS
          value: "sk-123456,sk-789012"
        resources:
          limits:
            memory: "16Gi"
            cpu: "4000m"
          requests:
            memory: "8Gi"
            cpu: "2000m"
        volumeMounts:
        - name: models
          mountPath: /models
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
      - name: logs
        persistentVolumeClaim:
          claimName: logs-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: llama-api-service
spec:
  selector:
    app: llama-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 31301
  type: LoadBalancer
```

## 配置管理

### 环境变量配置
```bash
# 模型配置
LLAMA_MODEL_PATH=/path/to/model.gguf
LLAMA_N_CTX=4096
LLAMA_N_THREADS=8
LLAMA_VERBOSE=false

# 资源配置
LLAMA_MAX_PROMPT_TOKENS=2048
LLAMA_MAX_TOTAL_TOKENS=4096
LLAMA_MAX_BATCH_SIZE=1

# 安全配置
LLAMA_API_KEYS=sk-123456,sk-789012
LLAMA_RATE_LIMIT_REQUESTS=100
LLAMA_RATE_LIMIT_WINDOW=60
LLAMA_MAX_CONCURRENT_REQUESTS=20

# 服务配置
LLAMA_HOST=0.0.0.0
LLAMA_PORT=31301
LLAMA_DEBUG=false
```

### 配置验证
- 部署前验证配置项的正确性
- 检查模型文件是否存在
- 验证API密钥格式

## 反向代理配置

### Nginx配置示例
```nginx
upstream llama_api {
    server localhost:31301;
    # 如果有多个实例
    # server localhost:31302;
    # server localhost:31303;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL证书配置
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # 限制请求体大小
    client_max_body_size 10M;

    location / {
        proxy_pass http://llama_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 监控和告警

### 应用监控
- 响应时间监控
- 错误率监控
- 并发请求数监控
- Token使用量统计

### 系统监控
- CPU使用率
- 内存使用率
- 磁盘空间
- 网络带宽

### 监控工具
- Prometheus + Grafana (推荐)
- ELK Stack (Elasticsearch, Logstash, Kibana)
- 自定义监控脚本

### 告警设置
- 响应时间超过阈值
- 错误率过高
- 资源使用率过高
- 服务不可用

## 日志管理

### 日志级别
- DEBUG: 详细调试信息
- INFO: 一般操作信息
- WARNING: 潜在问题
- ERROR: 错误事件
- CRITICAL: 严重错误

### 日志格式
- 结构化日志 (JSON格式)
- 包含请求ID用于追踪
- 记录时间戳、级别、消息

### 日志轮转
- 按大小或时间轮转
- 保留策略 (如保留最近30天)
- 压缩旧日志文件

## 安全措施

### 网络安全
- 使用HTTPS/TLS加密
- 限制IP访问 (可选)
- DDoS防护

### 认证授权
- 强制使用API密钥
- 定期轮换密钥
- 实现速率限制

### 数据安全
- 不在日志中记录敏感信息
- 加密存储API密钥
- 安全处理错误信息

## 备份和恢复

### 配置备份
- 定期备份配置文件
- 版本控制配置变更
- 自动化备份脚本

### 数据备份
- 如果有持久化数据，定期备份
- 验证备份完整性
- 测试恢复流程

## 故障处理

### 常见故障
- 模型加载失败
- 内存不足
- API访问被拒
- 响应时间过长

### 故障诊断
- 查看应用日志
- 检查系统资源
- 验证配置正确性
- 检查网络连接

### 应急预案
- 服务降级策略
- 快速回滚流程
- 备用服务实例

## 性能调优

### 参数调优
- 调整线程数 (`LLAMA_N_THREADS`)
- 调整上下文长度 (`LLAMA_N_CTX`)
- 调整并发数限制
- 调整批处理大小

### 硬件优化
- 使用更快的存储 (SSD)
- 增加内存容量
- 使用GPU加速 (如支持)

### 缓存策略
- 实现适当的响应缓存
- 优化Token计算缓存
- 数据库查询缓存 (如适用)

## 滚动更新

### 部署策略
- 蓝绿部署
- 金丝雀发布
- 滚动更新

### 更新检查清单
- 备份当前版本
- 验证新版本配置
- 测试关键功能
- 监控更新过程

## 运维自动化

### CI/CD流水线
- 自动化测试
- 自动化部署
- 自动化回滚

### 健康检查
- 定期健康检查
- 自动重启失败实例
- 自动扩缩容 (如支持)

## 文档和知识库

### 运维文档
- 部署指南
- 故障处理手册
- 配置参数说明
- 性能调优指南

### 知识库
- 常见问题解答
- 最佳实践
- 性能基准数据

## 最佳实践

1. 使用容器化部署以确保环境一致性
2. 实施全面的监控和告警
3. 定期进行安全审计
4. 实现自动化测试和部署
5. 维护详细的运维文档
6. 定期进行灾难恢复演练
7. 优化资源配置以降低成本
8. 实施最小权限原则