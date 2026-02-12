# 依赖管理开发指南

## 概述

依赖管理是确保项目稳定运行和可维护性的关键环节。本指南详细描述了项目的依赖管理策略、工具选择、版本控制和安全更新等内容。

## 依赖分类

### 1. 核心依赖
- **FastAPI** - Web框架
- **llama-cpp-python** - 模型推理引擎
- **Pydantic** - 数据校验和配置管理
- **Uvicorn/Gunicorn** - ASGI服务器

### 2. 开发依赖
- **pytest** - 测试框架
- **mypy** - 静态类型检查
- **black** - 代码格式化
- **flake8** - 代码质量检查
- **pre-commit** - 预提交钩子

### 3. 可选依赖
- **Redis** - 缓存和限流（可选）
- **Prometheus** - 监控（可选）
- **Requests** - HTTP客户端

## 依赖管理工具

### 1. pip + requirements.txt
- 使用requirements.txt管理依赖
- 区分生产依赖和开发依赖
- 使用requirements-dev.txt管理开发依赖

### 2. Poetry (推荐)
- 更好的依赖解析
- 虚拟环境管理
- 语义化版本控制
- 锁文件支持

### 3. pipenv
- Pipfile和Pipfile.lock
- 虚拟环境集成
- 依赖图可视化

## 版本控制策略

### 1. 语义化版本控制
- 主版本号：不兼容的API变更
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 2. 版本锁定
- 生产环境使用精确版本
- 开发环境允许次要版本更新
- 定期更新依赖版本

### 3. 兼容性策略
- 向后兼容承诺
- 废弃警告策略
- 迁移指南提供

## 依赖安全

### 1. 安全扫描
- 定期进行依赖漏洞扫描
- 使用safety或pip-audit工具
- 集成CI/CD流水线

### 2. 信任源管理
- 只从可信源安装包
- 使用私有PyPI镜像（如需要）
- 验证包签名

### 3. 依赖最小化
- 移除不必要的依赖
- 审查间接依赖
- 定期清理依赖树

## requirements.txt 结构

### 生产依赖 (requirements.txt)
```
fastapi==0.104.1
llama-cpp-python==0.2.50
pydantic==2.5.0
uvicorn==0.24.0
gunicorn==21.2.0
pydantic-settings==2.1.0
typing-extensions>=4.8.0
jinja2>=3.1.2
```

### 开发依赖 (requirements-dev.txt)
```
-r requirements.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
mypy==1.7.1
black==23.10.1
flake8==6.1.0
safety==2.4.0b4
pre-commit==3.5.0
```

## Poetry配置 (pyproject.toml)

```toml
[tool.poetry]
name = "osins-llama"
version = "1.0.0"
description = "Production-ready LLM API service compatible with OpenAI API"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.8"
fastapi = "^0.104.0"
llama-cpp-python = "^0.2.50"
pydantic = "^2.5.0"
uvicorn = "^0.24.0"
gunicorn = "^21.2.0"
pydantic-settings = "^2.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
mypy = "^1.7.0"
black = "^23.10.0"
flake8 = "^6.1.0"
safety = "^2.4.0"
pre-commit = "^3.5.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

## 依赖更新策略

### 1. 定期更新
- 每月检查依赖更新
- 优先更新安全补丁
- 测试更新后的兼容性

### 2. 自动化更新
- 使用Dependabot自动创建PR
- 集成安全扫描工具
- 自动测试验证

### 3. 版本冻结
- 生产环境版本冻结
- 预发布环境测试更新
- 逐步推进版本更新

## 依赖验证

### 1. 类型检查
- 使用mypy进行静态类型检查
- 验证依赖的类型注解
- 检查兼容性问题

### 2. 兼容性测试
- 运行完整测试套件
- 验证API兼容性
- 检查性能影响

### 3. 安全检查
- 扫描已知漏洞
- 验证依赖来源
- 检查许可证兼容性

## 虚拟环境管理

### 1. 环境隔离
- 为每个项目创建独立环境
- 使用venv或virtualenv
- 避免全局污染

### 2. 环境配置
- 自动激活脚本
- 环境变量管理
- 路径配置

### 3. 环境共享
- 提供环境配置说明
- 使用requirements.txt
- 支持Docker环境

## Docker依赖管理

### 1. 多阶段构建
```
# 第一阶段：依赖安装
FROM python:3.10-slim as deps-installer
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 第二阶段：应用构建
FROM python:3.10-slim
WORKDIR /app
COPY --from=deps-installer /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 依赖缓存
- 利用Docker层缓存
- 分离依赖安装和代码复制
- 减少构建时间

## 监控和审计

### 1. 依赖审计
- 定期审计依赖树
- 识别废弃依赖
- 检查许可证合规

### 2. 性能监控
- 监控依赖性能
- 识别瓶颈依赖
- 评估替代方案

### 3. 安全监控
- 持续安全扫描
- 漏洞预警系统
- 应急响应计划

## 最佳实践

### 1. 依赖声明
- 明确声明所有依赖
- 区分直接和间接依赖
- 提供依赖用途说明

### 2. 版本策略
- 使用兼容性版本运算符
- 定期评估版本更新
- 平衡稳定性和功能

### 3. 安全措施
- 定期安全扫描
- 验证依赖来源
- 监控安全公告

### 4. 文档化
- 维护依赖清单
- 记录选择理由
- 提供更新指南

## 工具配置

### 1. pre-commit hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.10.1
    hooks:
      - id: black
        language_version: python3.10
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
      
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
```

### 2. 安全扫描配置
```bash
# 定期运行安全扫描
safety check -r requirements.txt
pip-audit
```

### 3. 依赖分析
```bash
# 分析依赖树
pipdeptree
pip list --outdated
```

## 迁移策略

### 1. 依赖升级
- 评估升级影响
- 运行兼容性测试
- 准备回滚方案

### 2. 依赖替换
- 评估替代方案
- 迁移路径规划
- 渐进式替换

### 3. 版本回退
- 维护旧版本兼容
- 快速回退机制
- 用户通知流程

## 依赖管理流程

1. **需求分析** - 确定需要的新依赖
2. **评估选择** - 评估多个选项的优劣
3. **安全检查** - 扫描潜在安全风险
4. **兼容测试** - 验证与现有系统的兼容性
5. **集成测试** - 运行完整测试套件
6. **文档更新** - 更新相关文档
7. **发布部署** - 在受控环境中部署
8. **监控反馈** - 监控运行状态和性能

## 总结

有效的依赖管理是确保项目长期健康发展的重要因素。通过采用合适的工具、制定明确的策略、实施严格的安全措施，我们可以确保项目的稳定性和安全性，同时保持技术栈的现代化。