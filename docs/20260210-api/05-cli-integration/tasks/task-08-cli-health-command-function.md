# health命令函数实现

## 概述

health命令用于执行服务器健康检查。

## 实现要求

1. 实现health命令的Click装饰器
2. 定义必要的参数选项
3. 验证参数的有效性
4. 调用健康检查逻辑
5. 处理健康检查过程中的异常

## 代码实现

```python
import click


@click.command()
@click.option('--api-url', default='http://localhost:31301', help='API endpoint URL')
@click.option('--timeout', default=30, type=int, help='Timeout in seconds')
def health(api_url: str, timeout: int):
    """Perform health check."""
    from src.llama.cli.health import execute_health
    
    # Execute health command
    execute_health(
        api_url=api_url,
        timeout=timeout
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

- 验证API URL格式安全性
- 验证超时值范围有效性
- 防止恶意URL注入
- 验证URL格式有效性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12