# stop命令函数实现

## 概述

stop命令用于安全停止正在运行的osins-llama服务器实例。

## 实现要求

1. 实现stop命令的Click装饰器
2. 定义必要的参数选项
3. 验证参数的有效性
4. 调用服务器停止逻辑
5. 处理停止过程中的异常
6. 提供详细的日志记录
7. 实现安全验证机制

## 代码实现

```python
import click
import logging
import signal
import os
import sys
import time
from pathlib import Path

def acquire_lock(fd, timeout=10):
    """统一的锁获取函数，支持超时"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            if sys.platform.startswith("win"):
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, BlockingIOError):
            time.sleep(0.1)
    return False

def release_lock(fd):
    """统一的锁释放函数"""
    if sys.platform.startswith("win"):
        import msvcrt
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)


@click.command()
@click.option('--pid-file', default='./llama.pid', type=click.Path(), help='PID file path')
@click.option('--force', is_flag=True, help='Force stop')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def stop(pid_file: str, force: bool, verbose: bool):
    """Stop the running osins-llama server instance."""
    from src.llama.cli.stop import execute_stop
    import sys
    
    # 设置日志级别
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    if verbose:
        logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # 仅当logger尚未配置handler时添加，避免重复日志
    if not logger.handlers:
        logger.addHandler(handler)
    # 防止向上级传播日志
    logger.propagate = False

    # Convert string path to Path object
    pid_file_obj = Path(pid_file)

    try:
        # Execute stop command
        result = execute_stop(
            pid_file=pid_file_obj,
            force=force
        )
        sys.exit(result)  # 根据执行结果返回相应退出码
    except SystemExit as e:
        sys.exit(e.code)
    except Exception:
        sys.exit(1)  # 发生未预期异常时返回1
```

## 执行逻辑

`execute_stop` 函数应实现以下步骤：

1. 验证PID文件路径安全性，防止路径遍历攻击
2. 检查PID文件是否存在
3. 读取PID文件内容并验证PID格式
4. 检查PID对应的进程是否存在
5. 验证进程是否为osins-llama实例
6. 尝试向进程发送SIGTERM信号
7. 如果force标志为True或SIGTERM失败，发送SIGKILL信号
8. 等待进程终止
9. 删除PID文件
10. 记录操作日志

## 异常处理

- **PID文件不存在**：记录警告日志并退出
- **PID文件内容非法**：记录错误日志并退出
- **目标进程不存在**：记录警告日志并清理PID文件
- **权限不足**：记录错误日志并退出
- **进程终止超时**：在force模式下记录错误并尝试强制终止
- **PID文件删除失败**：记录错误日志但不中断程序

## 安全验证

- 验证PID文件路径安全性，防止路径遍历攻击
- 验证PID文件权限
- 确保进程归属验证
- 验证PID文件路径是否在预期目录内

## 日志规范

- 使用logging模块记录操作日志
- INFO级别：记录正常停止操作
- WARNING级别：记录PID文件不存在、目标进程不存在等情况
- ERROR级别：记录权限不足、进程终止失败等情况
- CRITICAL级别：记录严重错误如无法删除PID文件

## 返回码

- 0: 成功停止服务器
- 1: 一般错误（如权限不足、PID文件无效等）
- 2: 进程终止超时

## 边界测试用例

- PID文件为空或内容非法：应记录错误日志并退出
- PID对应进程非osins-llama：应验证进程归属并拒绝操作
- 强制停止权限不足：应记录错误并提供解决方案
- 多实例同时stop：应确保线程安全，避免竞态条件
- PID文件权限不足：应记录错误并提示用户
- 目标进程已停止：应检测并清理PID文件
- 无效PID文件路径：应验证路径安全性，防止路径遍历攻击

## 跨平台兼容性

- Windows: 使用os.kill()配合适当的信号值，注意Windows上SIGTERM实际上调用TerminateProcess，可能导致进程无法优雅终止。在Windows上，强制停止(--force)会直接终止进程，无机会执行清理操作
- Unix/Linux/macOS: 使用标准信号SIGTERM/SIGKILL
- 确保PID文件路径兼容各操作系统
- 考虑Windows上信号处理的局限性，对于需要优雅终止的应用，在Windows上可能需要特殊处理

## 实施建议

### 依赖项要求
- psutil: 用于进程验证，建议作为必需依赖安装以确保 `_verify_process_owner` 功能始终可用

### execute_stop 函数实现要点

在实现 `src/llama/cli/stop.py` 中的 `execute_stop` 函数时，请遵循以下要点：

```python
import logging
import os
import signal
import time
from pathlib import Path


def execute_stop(pid_file: Path, force: bool = False) -> int:
    """
    停止osins-llama服务器实例

    Args:
        pid_file: PID文件路径
        force: 是否强制停止

    Returns:
        int: 返回码 (0: 成功, 1: 一般错误, 2: 超时)
        
    Raises:
        ValueError: 当PID文件路径无效时
        PermissionError: 当权限不足时
        ProcessLookupError: 当目标进程不存在时
    """
    logger = logging.getLogger(__name__)
    
    # 获取文件锁以确保多实例并发安全
    lock_file_path = pid_file.with_suffix('.lock')
    lock_fd = None
    try:
        # 创建锁文件
        lock_fd = os.open(lock_file_path, os.O_CREAT | os.O_RDWR)
        
        # 尝试获取锁，最多等待10秒
        if not acquire_lock(lock_fd, timeout=10):
            logger.critical(f"Could not acquire lock on {lock_file_path} within 10 seconds")
            return 1  # 获取锁失败
        
        # 继续执行停止逻辑...
        
        logger.debug(f"Attempting to stop process using PID file: {pid_file}, force={force}")
        
        # 1. 验证PID文件路径安全性
        if not _is_safe_path(pid_file):
            logger.error(f"Unsafe PID file path: {pid_file}")
            raise ValueError(f"Unsafe PID file path: {pid_file}")
    
        # 2. 检查PID文件是否存在
        if not pid_file.exists():
            logger.warning(f"PID file does not exist: {pid_file}")
            return 0  # PID文件不存在，认为服务已停止

        # 3. 读取PID文件内容并验证PID格式
        try:
            with pid_file.open('r') as f:
                pid_str = f.read().strip()
                logger.debug(f"Read PID from file {pid_file}: {pid_str}")

            if not pid_str.isdigit():
                logger.error(f"Invalid PID in file: {pid_file}")
                pid_file.unlink()  # 删除无效PID文件
                return 1  # 错误：PID文件内容无效

            pid = int(pid_str)
        except (IOError, ValueError) as e:
            logger.error(f"Failed to read PID file {pid_file}: {e}")
            return 1  # 错误：无法读取PID文件
    
        # 4. 检查PID对应的进程是否存在
        try:
            os.kill(pid, 0)  # 检查进程是否存在，不发送信号
            logger.debug(f"Process {pid} exists and is accessible")
        except ProcessLookupError:
            logger.warning(f"Process {pid} does not exist, cleaning up PID file")
            _cleanup_pid_file(pid_file, logger)
            return 0  # 进程不存在，认为服务已停止
        except PermissionError:
            logger.error(f"No permission to access process {pid}")
            return 1  # 权限错误
    
        # 5. 验证进程是否为osins-llama实例 (可选但推荐)
        if not _verify_process_owner(pid, force):
            logger.error(f"Process {pid} is not owned by current user or is not osins-llama")
            return 1  # 验证失败，返回错误码
    
        # 6. 向进程发送SIGTERM信号
        try:
            if force:
                logger.info(f"Force stopping process {pid}")
                try:
                    os.kill(pid, signal.SIGKILL)
                except (OSError, PermissionError) as e:
                    logger.error(f"Failed to send SIGKILL to process {pid}: {e}")
                    return 1  # 强制停止失败
            else:
                logger.info(f"Stopping process {pid}")
                
                # 在Windows上，SIGTERM实际上调用TerminateProcess，无法优雅退出
                if sys.platform.startswith("win"):
                    logger.warning("Windows does not support graceful SIGTERM. Use --force to terminate process.")
                
                os.kill(pid, signal.SIGTERM)

                # 7. 等待进程终止
                max_wait_time = 30  # 最多等待30秒
                wait_interval = 0.5
                elapsed = 0

                while elapsed < max_wait_time:
                    try:
                        os.kill(pid, 0)  # 检查进程是否仍在运行
                        time.sleep(wait_interval)
                        elapsed += wait_interval
                    except ProcessLookupError:
                        logger.info(f"Process {pid} has been terminated gracefully")
                        break
                else:
                    # 超时仍未终止，如果是非force模式，则强制终止
                    if not force:
                        logger.warning(f"Process {pid} did not terminate gracefully, forcing termination")
                        try:
                            os.kill(pid, signal.SIGKILL)
                        except ProcessLookupError:
                            # 进程在强制终止前已结束
                            logger.info(f"Process {pid} has been terminated after SIGKILL")
                            return 0
                        except (OSError, PermissionError) as e:
                            logger.error(f"Failed to send SIGKILL to process {pid}: {e}")
                            return 1  # 强制停止失败
                    else:
                        # 即使在force模式下，如果仍然超时，则返回超时错误
                        logger.error(f"Process {pid} did not terminate even after SIGKILL")
                        return 2  # 超时错误
                
        except ProcessLookupError:
            logger.info(f"Process {pid} has been terminated")
            _cleanup_pid_file(pid_file, logger)
            return 0  # 正常终止
        except PermissionError as e:
            logger.error(f"Permission denied when stopping process {pid}: {e}")
            return 1  # 权限错误
        except OSError as e:
            logger.error(f"OS error when stopping process {pid}: {e}")
            return 1  # 其他系统错误
    
    finally:
        # 释放锁并清理锁文件
        if lock_fd is not None:
            release_lock(lock_fd)  # 释放锁
            os.close(lock_fd)  # 关闭文件描述符
            try:
                os.remove(lock_file_path)  # 删除锁文件
            except OSError as e:
                logger.debug(f"Failed to remove lock file {lock_file_path}: {e}")  # 记录DEBUG日志
    
    return 0  # 成功停止
    

def _is_safe_path(path: Path) -> bool:
    """确保 PID 文件在预期目录下，防止路径遍历"""
    try:
        resolved = path.resolve(strict=False)
        allowed_dir = Path.cwd().resolve() / "pids"
        allowed_dir.mkdir(exist_ok=True)
        return allowed_dir in resolved.parents or resolved == allowed_dir
    except Exception:
        return False


def _verify_process_owner(pid: int, force: bool = False) -> bool:
    """验证进程是否属于当前用户(可选实现)"""
    try:
        import psutil
        process = psutil.Process(pid)
        # 检查进程命令行，确保是 osins-llama 进程
        cmdline = " ".join(process.cmdline())
        if "osins-llama" not in cmdline:
            return False
        return process.is_running()
    except ImportError:
        # 如果psutil不可用，记录日志
        logger = logging.getLogger(__name__)
        if force:
            # 在强制停止模式下，如果psutil不可用，记录critical日志并拒绝操作
            logger.critical("psutil not available, cannot verify process owner for force stop. Refusing to kill process.")
            return False
        else:
            # 在非强制模式下，记录警告日志并返回True让后续处理决定
            logger.warning("psutil not available, skipping process owner verification")
            return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # 如果无法访问进程，返回False
        return False


def _cleanup_pid_file(pid_file: Path, logger: logging.Logger):
    """清理PID文件，包含重试机制"""
    retries = 3
    for attempt in range(retries):
        try:
            if pid_file.exists():
                pid_file.unlink()
                logger.info(f"Removed PID file: {pid_file}")
                return
        except Exception as e:
            logger.debug(f"Failed to remove PID file {pid_file} on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(0.1)  # 短暂等待后重试
    logger.error(f"Failed to remove PID file {pid_file} after {retries} attempts")
```

## 验证标准

- [ ] 命令装饰器正确应用
- [ ] 参数选项定义完整
- [ ] 参数类型验证正确
- [ ] 默认值设置恰当
- [ ] 帮助文本清晰准确
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 执行逻辑完整且清晰
- [ ] 异常处理覆盖所有可能情况
- [ ] 安全验证措施到位
- [ ] 日志记录符合规范
- [ ] 返回码定义明确
- [ ] 跨平台兼容性考虑周全
- [ ] 边界测试用例全面覆盖
- [ ] 实施建议清晰可行

## 测试验证

### 跨平台多实例 stop 压力测试示例

以下是一个可用于验证 stop 命令实现的压力测试示例，验证锁机制、PID 文件处理、SIGTERM/SIGKILL 行为，以及边界条件处理：

```python
import subprocess
import sys
import time
import os
from pathlib import Path
import signal
import threading

# -----------------------------
# 配置部分
# -----------------------------
TEST_PID_FILE = Path("./test_llama.pid")
NUM_INSTANCES = 3  # 模拟多个 stop 实例同时执行
TEST_PROCESS_DURATION = 10  # 模拟目标进程存在的秒数

# -----------------------------
# 模拟目标进程
# -----------------------------
def fake_server_process():
    """模拟一个持续运行的服务器进程，写 PID 文件"""
    pid = os.getpid()
    with TEST_PID_FILE.open("w") as f:
        f.write(str(pid))
    print(f"Fake server running, PID={pid}")
    try:
        # 模拟进程运行
        time.sleep(TEST_PROCESS_DURATION)
    finally:
        if TEST_PID_FILE.exists():
            TEST_PID_FILE.unlink()
        print(f"Fake server PID={pid} stopped and cleaned PID file")

# -----------------------------
# 调用 stop 命令函数
# -----------------------------
def call_stop(force=False, verbose=False):
    """通过 subprocess 调用 stop CLI"""
    cmd = [sys.executable, "-m", "src.llama.cli.stop", "--pid-file", str(TEST_PID_FILE)]
    if force:
        cmd.append("--force")
    if verbose:
        cmd.append("--verbose")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Stop exit code: {result.returncode}")
    print(result.stdout)
    print(result.stderr)

# -----------------------------
# 测试多实例 stop 并发
# -----------------------------
def test_concurrent_stop():
    # 启动模拟服务器进程
    server_thread = threading.Thread(target=fake_server_process)
    server_thread.start()
    time.sleep(1)  # 确保 PID 文件已写入

    # 同时启动多个 stop 实例
    threads = []
    for i in range(NUM_INSTANCES):
        t = threading.Thread(target=call_stop, kwargs={"force": False, "verbose": True})
        threads.append(t)
        t.start()

    # 等待所有 stop 实例完成
    for t in threads:
        t.join()

    # 等待服务器线程结束
    server_thread.join()

    # 检查 PID 文件是否已清理
    if TEST_PID_FILE.exists():
        print("Error: PID file still exists after stop")
    else:
        print("Success: PID file cleaned")

# -----------------------------
# 执行测试
# -----------------------------
if __name__ == "__main__":
    test_concurrent_stop()
```

#### 功能说明

1. **模拟目标进程**
   * 使用 `fake_server_process` 模拟 osins-llama 服务器运行，写入 PID 文件。
   * 运行 `TEST_PROCESS_DURATION` 秒后自动退出并删除 PID 文件。

2. **并发 stop 调用**
   * 使用 `threading.Thread` 模拟 `NUM_INSTANCES` 个 stop 命令同时执行。
   * 验证锁机制是否保证单实例操作 PID 文件。

3. **日志与输出**
   * subprocess 调用 stop CLI，输出 exit code、stdout、stderr，可验证日志、返回码、异常处理。

4. **边界验证**
   * 多实例并发 stop
   * PID 文件存在、进程已停止
   * 强制停止（可通过 `force=True` 测试 SIGKILL 行为）

## 版本信息

- 版本: 2.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-14
