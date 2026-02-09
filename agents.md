# Llama CLI Project Agents Guide

## 项目概述
这是一个基于llama_cpp的命令行工具，用于管理和运行LLM模型服务。

## 项目结构
```
llama/
├── .flake8            # Flake8配置文件
├── .gitignore         # Git忽略文件配置
├── agents.md          # 项目规范文档
├── docs/              # 文档目录
├── LICENSE            # 许可证文件
├── pyproject.toml     # 项目配置文件
├── README.md          # 项目说明文档
├── requirements.txt   # 生产环境依赖
├── requirements-dev.txt # 开发环境依赖
├── scripts/           # 脚本目录
├── setup.cfg          # Setup配置文件
├── setup.py           # 项目配置文件
├── src/               # 源代码目录
│   └── llama/         # 源代码包
│       ├── __init__.py
│       ├── _version.py # 版本信息
│       ├── main.py    # CLI入口点
│       ├── api/       # 接口层
│       ├── config/    # 配置
│       ├── core/      # 核心逻辑
│       │   └── commands/ # 命令模块目录
│       │       ├── __init__.py
│       │       ├── start.py   # start命令实现
│       │       ├── restart.py # restart命令实现
│       │       ├── down.py    # down命令实现
│       │       └── status.py  # status命令实现
│       ├── models/    # 数据模型
│       ├── services/  # 服务层
│       └── utils/     # 工具函数
├── tests/             # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_main.py   # 主程序测试
│   ├── test_start.py  # start命令测试
│   ├── test_restart.py # restart命令测试
│   ├── test_down.py   # down命令测试
│   └── test_status.py # status命令测试
├── tox.ini            # 多版本测试配置
└── venv/              # 虚拟环境目录
```

## 技术栈
- Python 3.8+
- llama-cpp-python
- click (命令行解析)

## 代码规范
- 遵循PEP 8代码风格
- 每个函数或类必须放在单独的py文件中
- 不允许一个py文件中包含多个函数或类
- 所有函数和类必须配有单元测试
- 单元测试保存在tests目录中
- 使用src目录隔离源代码
- 按功能模块组织代码到相应子目录

## 环境设置
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖
pip install llama-cpp-python

# 安装项目 (开发模式)
pip install -e .
```

## 命令说明
- `llama start -p 31301 -m ./qwen2.5-7b-instruct-uncensored-q4_k_m.gguf` - 启动LLM服务
- `llama restart` - 重启LLM服务
- `llama down` - 停止LLM服务
- `llama status` - 查看LLM服务状态
- `llama --help` - 显示帮助信息

## 测试命令
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_start.py

# 运行测试并显示详细输出
pytest -v

# 运行测试并生成覆盖率报告
pytest --cov=llama
```

## 开发指南
1. 每个新功能必须创建独立的模块文件
2. 必须编写对应的单元测试
3. 提交前确保所有测试通过
4. 遵循单一职责原则，每个文件只负责一个功能
5. 按照功能将代码组织到相应的目录(api, core, models, services, utils)
6. 使用src目录隔离源代码，便于打包和发布
7. 遵循标准Python项目结构规范