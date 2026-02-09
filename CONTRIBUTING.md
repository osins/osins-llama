# 贡献指南

感谢您有兴趣为 Llama CLI 项目做贡献！本文档提供了有关如何参与此项目的指南。

## 开发环境设置

1. Fork 此仓库
2. 克隆您的 fork 到本地：
```bash
git clone https://github.com/YOUR_USERNAME/llama.git
cd llama
```

3. 创建虚拟环境并安装依赖：
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
pip install -r requirements-dev.txt
```

## 代码规范

- 遵循 PEP 8 代码风格
- 每个函数或类必须放在单独的 .py 文件中
- 不允许一个 .py 文件中包含多个函数或类
- 所有函数和类必须配有单元测试
- 使用 src 目录隔离源代码
- 按功能模块组织代码到相应子目录

## 提交更改

1. 创建新分支：
```bash
git checkout -b feature/your-feature-name
```

2. 进行更改并确保所有测试通过：
```bash
pytest
```

3. 提交更改：
```bash
git add .
git commit -m "描述您的更改"
```

4. 推送到远程分支：
```bash
git push origin feature/your-feature-name
```

5. 创建 Pull Request

## 测试

在提交更改之前，请确保所有测试都通过：

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_start.py

# 运行测试并显示详细输出
pytest -v
```

## 代码结构

项目遵循标准 Python 项目结构：

- `src/llama/core/commands/` - 命令实现
- `tests/` - 测试文件
- `docs/` - 文档
- `scripts/` - 脚本

## 报告问题

如果您发现错误或有改进建议，请在 GitHub 上创建 issue。请提供以下信息：

- 问题的详细描述
- 重现步骤
- 预期行为
- 实际行为
- 您的环境信息

## 联系方式

如有疑问，请通过 GitHub issue 联系项目维护者。