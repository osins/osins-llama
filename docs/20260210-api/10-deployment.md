# 部署开发指南

## 概述

部署是将应用程序从开发环境转移到生产环境的过程。本指南详细描述了部署的策略、方法、工具和最佳实践，确保系统能够稳定、安全、高效地运行。

## 部署策略

### 1. 部署类型

#### 蓝绿部署
- 维护两个相同的生产环境（蓝色和绿色）
- 一个环境运行当前版本，另一个部署新版本
- 通过切换路由实现无缝更新
- 降低部署风险，便于快速回滚

#### 金丝雀发布
- 逐步将新版本部署给一小部分用户
- 监控新版本的表现
- 逐步扩大新版本的流量比例
- 降低新版本对所有用户的影响

#### 滚动更新
- 逐步替换旧版本实例
- 保持服务连续性
- 适用于无状态应用
- 减少资源消耗

### 2. 部署环境

#### 开发环境
- 用于日常开发和测试
- 配置相对宽松
- 便于调试和快速迭代

#### 测试环境
- 用于功能验证和集成测试
- 配置接近生产环境
- 验证新功能的完整性

#### 预生产环境
- 与生产环境完全相同
- 用于最终验证
- 模拟真实生产场景

#### 生产环境
- 面向最终用户的环境
- 配置最严格
- 注重安全和稳定性

## 容器化部署

### 1. Docker部署

#### Dockerfile最佳实践
```dockerfile
# 使用官方基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app
USER app

# 暴露端口
EXPOSE 31301

# 启动命令
CMD ["gunicorn", "src.server.app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:31301"]
```

#### Docker Compose配置
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
      - ./models:/models:ro
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:31301/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### 2. 容器编排

#### Kubernetes部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llama-api
  labels:
    app: llama-api
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
          valueFrom:
            secretKeyRef:
              name: llama-secrets
              key: api-keys
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
          readOnly: true
        - name: logs
          mountPath: /app/logs
        livenessProbe:
          httpGet:
            path: /v1/health
            port: 31301
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /v1/health
            port: 31301
          initialDelaySeconds: 30
          periodSeconds: 10
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

## 传统部署

### 1. 直接部署

#### 环境准备
```bash
# 创建应用目录
sudo mkdir -p /opt/llama-api
sudo chown app:app /opt/llama-api

# 创建虚拟环境
python -m venv /opt/llama-api/venv
source /opt/llama-api/venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 服务配置 (systemd)
```ini
[Unit]
Description=LLaMA API Service
After=network.target

[Service]
Type=simple
User=app
Group=app
WorkingDirectory=/opt/llama-api
Environment=PATH=/opt/llama-api/venv/bin
Environment=LLAMA_MODEL_PATH=/opt/models/model.gguf
Environment=LLAMA_N_CTX=4096
Environment=LLAMA_N_THREADS=8
ExecStart=/opt/llama-api/venv/bin/gunicorn src.server.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:31301
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. 进程管理

#### 使用Supervisor
```ini
[program:llama-api]
command=/opt/llama-api/venv/bin/gunicorn src.server.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:31301
directory=/opt/llama-api
user=app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/llama-api.log
environment=LLAMA_MODEL_PATH="/opt/models/model.gguf",LLAMA_N_CTX="4096"
```

## 配置管理

### 1. 环境变量配置
```bash
# 核心配置
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

### 2. 配置文件管理
```yaml
# config.yaml
server:
  host: "0.0.0.0"
  port: 31301
  debug: false
  workers: 4

model:
  path: "/models/model.gguf"
  n_ctx: 4096
  n_threads: 8
  verbose: false

security:
  api_keys: ["sk-123456", "sk-789012"]
  rate_limit_requests: 100
  rate_limit_window: 60

performance:
  max_concurrent_requests: 20
  max_prompt_tokens: 2048
  max_total_tokens: 4096
```

## 反向代理配置

### 1. Nginx配置
```nginx
upstream llama_api {
    server localhost:31301 weight=1 max_fails=3 fail_timeout=30s;
    server localhost:31302 weight=1 max_fails=3 fail_timeout=30s;
    # 添加更多实例以实现负载均衡
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL证书配置
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # 限制请求体大小
    client_max_body_size 10M;

    location / {
        proxy_pass http://llama_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 健康检查端点
    location /health {
        access_log off;
        proxy_pass http://llama_api/v1/health;
    }
}
```

### 2. Apache配置
```apache
<VirtualHost *:443>
    ServerName api.yourdomain.com
    
    SSLEngine on
    SSLCertificateFile /path/to/certificate.crt
    SSLCertificateKeyFile /path/to/private.key
    
    # 反向代理配置
    ProxyPreserveHost On
    ProxyPass / http://localhost:31301/
    ProxyPassReverse / http://localhost:31301/
    
    # 超时设置
    ProxyTimeout 60
    
    # 安全头
    Header always set X-Frame-Options "DENY"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
</VirtualHost>
```

## 监控和日志

### 1. 应用监控
- 请求处理时间
- 错误率监控
- 并发请求数监控
- Token使用量统计

### 2. 系统监控
- CPU使用率
- 内存使用率
- 磁盘空间
- 网络带宽

### 3. 日志管理
- 结构化日志格式
- 日志轮转策略
- 集中日志收集
- 日志分析和告警

## 安全措施

### 1. 网络安全
- 使用HTTPS/TLS加密
- 限制IP访问（可选）
- DDoS防护
- WAF（Web应用防火墙）

### 2. 认证授权
- API密钥验证
- 定期轮换密钥
- 实现速率限制
- 访问控制列表

### 3. 数据安全
- 不在日志中记录敏感信息
- 加密存储API密钥
- 安全处理错误信息

## 备份和恢复

### 1. 配置备份
- 定期备份配置文件
- 版本控制配置变更
- 自动化备份脚本

### 2. 数据备份（如适用）
- 定期备份持久化数据
- 验证备份完整性
- 测试恢复流程

## 故障处理

### 1. 常见故障
- 模型加载失败
- 内存不足
- API访问被拒
- 响应时间过长

### 2. 故障诊断
- 查看应用日志
- 检查系统资源
- 验证配置正确性
- 检查网络连接

### 3. 应急预案
- 服务降级策略
- 快速回滚流程
- 备用服务实例

## 性能调优

### 1. 参数调优
- 调整线程数 (LLAMA_N_THREADS)
- 调整上下文长度 (LLAMA_N_CTX)
- 调整并发数限制
- 调整批处理大小

### 2. 硬件优化
- 使用更快的存储 (SSD)
- 增加内存容量
- 使用GPU加速（如支持）

### 3. 缓存策略
- 实现适当的响应缓存
- 优化Token计算缓存
- 数据库查询缓存（如适用）

## 部署自动化

### 1. CI/CD流水线
- 自动化测试
- 自动化构建
- 自动化部署
- 自动化回滚

### 2. 部署脚本
```bash
#!/bin/bash
# deploy.sh

set -e

APP_DIR="/opt/llama-api"
BACKUP_DIR="/opt/llama-api-backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting deployment..."

# 创建备份
if [ -d "$APP_DIR" ]; then
    echo "Creating backup..."
    cp -r "$APP_DIR" "${BACKUP_DIR}_${TIMESTAMP}"
fi

# 停止服务
echo "Stopping service..."
sudo systemctl stop llama-api || true

# 部署新版本
echo "Deploying new version..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"
git pull origin main

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 验证配置
echo "Validating configuration..."
python -c "from src.config import Config; Config()"

# 启动服务
echo "Starting service..."
sudo systemctl start llama-api

# 等待服务启动
sleep 10

# 验证服务状态
if curl -f http://localhost:31301/v1/health > /dev/null 2>&1; then
    echo "Deployment successful!"
else
    echo "Deployment failed! Rolling back..."
    sudo systemctl stop llama-api
    # 恢复备份
    sudo systemctl start llama-api
    exit 1
fi

echo "Deployment completed successfully!"
```

## 最佳实践

### 1. 部署前检查
- 验证配置文件正确性
- 检查模型文件完整性
- 确认依赖项安装正确

### 2. 部署过程
- 使用非root用户运行服务
- 设置适当的资源限制
- 配置健康检查和监控

### 3. 部署后验证
- 验证服务正常运行
- 检查日志输出
- 确认API端点可访问

### 4. 维护策略
- 定期更新依赖
- 监控资源使用
- 定期安全审计

## 总结

通过遵循这些部署指南和最佳实践，可以确保系统稳定、安全、高效地运行在生产环境中。关键是要根据具体需求选择合适的部署策略和工具，并建立完善的监控、日志和应急处理机制。