# ShellCommandService类实现

## 概述

ShellCommandService类实现了CommandService接口，提供执行shell命令的功能。

## 实现要求

1. 实现CommandService接口
2. 支持同步和异步命令执行
3. 提供命令执行结果
4. 处理命令执行过程中的异常
5. 记录执行时间和时间戳

## 代码实现

```python
import subprocess
import asyncio
import time
from datetime import datetime
from typing import Optional


class ShellCommandService(CommandService):
    def execute(self, *args, **kwargs) -> CommandResult:
        start_time = time.time()
        timestamp = datetime.now()

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=kwargs.get('timeout', 30),
                **kwargs
            )
            execution_time = time.time() - start_time

            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode,
                execution_time=execution_time,
                timestamp=timestamp,
                command=' '.join(args) if args else None
            )
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                output="",
                error="Command timed out",
                exit_code=-1,
                execution_time=execution_time,
                timestamp=timestamp,
                command=' '.join(args) if args else None
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=execution_time,
                timestamp=timestamp,
                command=' '.join(args) if args else None
            )

    async def execute_async(self, *args, **kwargs) -> CommandResult:
        start_time = time.time()
        timestamp = datetime.now()

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **kwargs
            )
            stdout, stderr = await process.communicate()

            execution_time = time.time() - start_time

            return CommandResult(
                success=process.returncode == 0,
                output=stdout.decode() if stdout else "",
                error=stderr.decode() if stderr else "",
                exit_code=process.returncode or 0,
                execution_time=execution_time,
                timestamp=timestamp,
                command=' '.join(args) if args else None
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=execution_time,
                timestamp=timestamp,
                command=' '.join(args) if args else None
            )
```

## 验证标准

- [ ] CommandService接口实现完整
- [ ] 同步命令执行支持
- [ ] 异步命令执行支持
- [ ] 命令执行结果返回
- [ ] 异常处理机制
- [ ] 执行时间记录
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整

## 安全考虑

- 验证命令参数安全性
- 防止命令注入攻击
- 限制命令执行时间

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12