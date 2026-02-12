# 命令执行服务

## 概述

命令执行服务负责处理CLI的各种命令执行逻辑，包括服务器启动、停止、重启、状态检查等操作。

## 服务职责

- 提供统一的命令执行接口
- 处理命令执行结果和错误
- 管理命令执行生命周期
- 实现同步/异步执行策略

## 服务接口

### 通用命令服务

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    output: str
    error: str
    exit_code: int
    execution_time: float
    timestamp: datetime = None
    command: Optional[str] = None


class CommandService(ABC):
    """命令服务抽象基类"""
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> CommandResult:
        """执行命令"""
        pass
    
    @abstractmethod
    async def execute_async(self, *args, **kwargs) -> CommandResult:
        """异步执行命令"""
        pass
```

## 异常处理

- 命令执行失败时返回适当的退出码
- 记录错误信息到日志
- 实现重试机制（如需要）

## 重试与回退策略

```python
import time
from typing import Callable


def retry_on_failure(
    func: Callable, 
    max_retries: int = 3, 
    delay: float = 1.0, 
    backoff: float = 2.0
):
    """重试装饰器"""
    def wrapper(*args, **kwargs):
        retries = 0
        current_delay = delay
        
        while retries < max_retries:
            try:
                result = func(*args, **kwargs)
                if result.success:
                    return result
                else:
                    retries += 1
                    if retries < max_retries:
                        time.sleep(current_delay)
                        current_delay *= backoff
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    raise e
                time.sleep(current_delay)
                current_delay *= backoff
        
        return result
    return wrapper
```

## 执行约束

- 命令执行时间限制
- 资源使用限制
- 并发执行控制

## 异常类型区分

- 命令不存在 (exit_code: 127)
- 权限不足 (exit_code: 126)
- 执行超时 (exit_code: -1)
- 其他错误 (exit_code: 1)

## 示例用法

```python
import subprocess
import asyncio
import time


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

## 单元测试提示

建议测试以下场景：
- 成功命令执行
- 失败命令执行
- 异常情况（超时、权限不足等）
- 并发执行

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12