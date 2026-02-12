# start命令函数实现

## 概述

start命令用于启动osins-llama服务器实例，支持多种启动参数配置。

## 实现要求

1. 实现start命令的Click装饰器
2. 定义所有必要的参数选项
3. 验证参数的有效性
4. 调用服务器启动逻辑
5. 处理启动过程中的异常

## 代码实现

```python
import click
from pathlib import Path
from typing import Optional


@click.command()
@click.option('--model-path', type=click.Path(exists=True), help='Model file path')
@click.option('--host', default='0.0.0.0', help='Server bind address')
@click.option('--port', default=31301, type=int, help='Server port')
@click.option('--n-ctx', default=2048, type=int, help='Context length')
@click.option('--n-threads', default=8, type=int, help='Number of threads')
@click.option('--api-keys', help='API key list (comma separated)')
@click.option('--max-concurrent-requests', default=10, type=int, help='Max concurrent requests')
@click.option('--rate-limit-requests', default=60, type=int, help='Rate limit requests')
@click.option('--rate-limit-window', default=60, type=int, help='Rate limit window in seconds')
@click.option('--debug/--no-debug', default=False, help='Debug mode')
@click.option('--pid-file', default='./llama.pid', type=click.Path(), help='PID file path')
def start(
    model_path: Optional[str],
    host: str,
    port: int,
    n_ctx: int,
    n_threads: int,
    api_keys: Optional[str],
    max_concurrent_requests: int,
    rate_limit_requests: int,
    rate_limit_window: int,
    debug: bool,
    pid_file: str
):
    """Start the osins-llama server instance."""
    from src.llama.cli.start import execute_start
    
    # Convert string paths to Path objects
    model_path_obj = Path(model_path) if model_path else None
    pid_file_obj = Path(pid_file)
    
    # Execute start command
    execute_start(
        model_path=model_path_obj,
        host=host,
        port=port,
        n_ctx=n_ctx,
        n_threads=n_threads,
        api_keys=api_keys,
        max_concurrent_requests=max_concurrent_requests,
        rate_limit_requests=rate_limit_requests,
        rate_limit_window=rate_limit_window,
        debug=debug,
        pid_file=pid_file_obj
    )
```

## 验证标准

- [ ] 命令装饰器正确应用
- [ ] 所有参数选项定义完整
- [ ] 参数类型验证正确
- [ ] 默认值设置恰当
- [ ] 帮助文本清晰准确
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整

## 安全考虑

- 验证模型路径安全性
- 验证PID文件路径安全性
- 防止路径遍历攻击
- 验证端口范围有效性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12