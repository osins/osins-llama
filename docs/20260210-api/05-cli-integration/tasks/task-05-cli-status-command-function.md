# status命令函数实现

## 概述

status命令用于查看osins-llama服务器的运行状态。

## 实现要求

1. 实现status命令的Click装饰器
2. 定义必要的参数选项（PID文件、API URL、debug模式）
3. 验证参数的有效性
4. 调用服务器状态检查逻辑
5. 处理状态检查过程中的异常
6. 返回标准化的退出码

## 代码实现

```python
import click
from pathlib import Path


@click.command()
@click.option('--pid-file', default='./llama.pid', type=click.Path(), help='PID file path')
@click.option('--api-url', default='http://localhost:31301', help='API endpoint URL')
@click.option('--debug/--no-debug', default=False, help='Debug mode')
def status(pid_file: str, api_url: str, debug: bool):
    """Check the server running status."""
    from src.llama.cli.status import execute_status

    # Convert string path to Path object
    pid_file_obj = Path(pid_file)

    # Execute status command
    result_code = execute_status(
        pid_file=pid_file_obj,
        api_url=api_url,
        debug=debug
    )
    
    # Exit with appropriate code
    raise SystemExit(result_code)
```

## 验证标准

- [ ] 命令装饰器正确应用
- [ ] 参数选项定义完整（PID文件、API URL、debug模式）
- [ ] 参数类型验证正确
- [ ] 默认值设置恰当
- [ ] 帮助文本清晰准确
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制健全
- [ ] 退出码返回标准化
- [ ] 与execute_status函数集成正常

## 安全考虑

- 验证PID文件路径安全性
- 验证API URL格式有效性
- 捕获无效字符和非法路径
- 捕获和处理异常，防止程序崩溃

## 版本信息
- 版本: 2.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-14