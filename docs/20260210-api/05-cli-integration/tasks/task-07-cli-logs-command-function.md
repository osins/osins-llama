# logs命令函数实现

## 概述

logs命令用于查看服务器日志。

## 实现要求

1. 实现logs命令的Click装饰器
2. 定义必要的参数选项（包括follow、lines、log-file、debug）
3. 验证参数的有效性（特别是lines范围和log-file路径安全性）
4. 调用日志查看逻辑
5. 处理日志查看过程中的异常

## 代码实现

```python
import click
from pathlib import Path


@click.command()
@click.option('--follow', is_flag=True, help='Follow log file')
@click.option('--lines', default=50, type=click.IntRange(1, 10000), help='Show last N lines (max 10000)')
@click.option('--log-file', default='./llama.log', type=click.Path(), help='Log file path')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def logs(follow: bool, lines: int, log_file: str, debug: bool):
    """View server logs."""
    from src.llama.cli.logs import execute_logs

    # Convert string path to Path object
    log_file_obj = Path(log_file)

    # Execute logs command
    execute_logs(
        follow=follow,
        lines=lines,
        log_file=log_file_obj,
        debug=debug
    )
```

## 验证标准

- [ ] 命令装饰器正确应用
- [ ] 参数选项定义完整（包含新增的debug选项和lines范围限制）
- [ ] 参数类型验证正确（lines限制在1-10000范围内）
- [ ] 默认值设置恰当
- [ ] 帮助文本清晰准确
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 路径安全性得到验证（防止路径遍历）
- [ ] 大文件读取性能优化
- [ ] follow模式支持日志轮转检测
- [ ] 异常处理统一并有退出码
- [ ] 日志输出可配置化（通过debug选项）

## 安全考虑

- 验证日志文件路径安全性（使用Path.resolve()检查路径是否在允许目录内）
- 防止路径遍历攻击（检查是否包含符号链接及路径是否在指定目录下）
- 验证文件访问权限
- 防止日志文件过大导致的资源耗尽（限制显示的最大行数）
- 防止任意文件访问（通过目录白名单机制）

## 底层实现要求

以下是 `src.llama.cli.logs.execute_logs` 函数需要满足的技术要求：

### 路径与安全性检查
- 使用 `log_file.resolve(strict=False)` 获取绝对路径
- 判断日志文件是否在允许的目录下（如 `LOG_DIR`）
- 检查符号链接，决定是否允许访问

### 大文件读取优化
- 使用 `collections.deque` 的 `maxlen` 参数来高效获取最后 N 行
- 避免一次性加载整个文件到内存

### Follow模式增强
- 支持日志轮转（logrotate）后的文件变化检测
- 检查文件 inode 是否变化，自动重新打开文件
- 考虑使用 `watchdog` 库来监听文件变化

### 异常处理
- 统一异常处理并定义退出码：
  - 1：IO错误
  - 2：路径安全错误
- 便于脚本自动化或 CI/CD 环境判断

### 参数校验
- 确保行数限制在 1-10000 范围内
- 验证日志文件路径是否合法

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-14