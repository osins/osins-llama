# restart命令函数实现

## 概述

restart命令用于重启osins-llama服务器实例。

## 实现要求

1. 实现restart命令的Click装饰器
2. 定义必要的参数选项
3. 验证参数的有效性
4. 调用服务器重启逻辑
5. 处理重启过程中的异常

## 代码实现

```python
import click
from pathlib import Path
from typing import Optional


@click.command()
@click.option('--model-path', type=click.Path(exists=True), help='Model file path')
@click.option('--host', help='Server bind address')
@click.option('--port', type=int, help='Server port')
@click.option('--wait', default=5, type=int, help='Wait time in seconds')
@click.option('--pid-file', default='./llama.pid', type=click.Path(), help='PID file path')
def restart(
    model_path: Optional[str],
    host: Optional[str],
    port: Optional[int],
    wait: int,
    pid_file: str
):
    """Restart the osins-llama server instance."""
    from src.llama.cli.restart import execute_restart
    
    # Convert string paths to Path objects
    model_path_obj = Path(model_path) if model_path else None
    pid_file_obj = Path(pid_file)
    
    # Execute restart command
    execute_restart(
        model_path=model_path_obj,
        host=host,
        port=port,
        wait=wait,
        pid_file=pid_file_obj
    )
```

## 验证标准

- [ ] 命令装饰器正确应用
- [ ] 参数选项定义完整
- [ ] 参数类型验证正确
- [ ] 默认值设置恰当
- [ ] 帮助文本清晰准确
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整

## 安全考虑

- 验证模型路径安全性
- 验证PID文件路径安全性
- 防止路径遍历攻击
- 验证参数范围有效性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12