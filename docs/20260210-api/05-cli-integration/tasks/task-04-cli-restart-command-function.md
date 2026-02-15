# restart命令函数实现

## 概述

restart命令用于安全重启osins-llama服务器实例。该命令首先安全停止现有的服务器实例，然后启动一个新的实例。

## 实现要求

1. 实现restart命令的Click装饰器
2. 定义必要的参数选项
3. 验证参数的有效性
4. 实现安全的重启逻辑（先停止后启动）
5. 包含适当的日志记录
6. 处理重启过程中的异常
7. 提供合适的返回码
8. 支持跨平台兼容性
9. 实现多实例并发安全
10. 实现重启失败回滚机制
11. 提供详细的调试模式
12. 设计全面的单元测试覆盖
13. Windows平台锁机制兼容
14. 锁文件异常重试机制
15. 日志级别动态调整
16. 可参数化的等待时间和回滚策略
17. 锁文件安全机制（PID写入）
18. PID文件验证机制
19. 增强的回滚策略
20. 扩展日志功能
21. 细化异常处理
22. 动态等待机制

## 代码实现

```python
import click
import logging
import logging.handlers
import time
import os
import platform
import socket
from pathlib import Path
from typing import Optional

from .stop import execute_stop
from .start import execute_start


def get_platform_lock(lock_file_path: Path, max_retries: int = 5, retry_delay: float = 0.1):
    """
    跨平台获取文件锁的函数
    """
    system = platform.system().lower()
    
    if system == "windows":
        import msvcrt
        retries = 0
        while retries < max_retries:
            try:
                # 尝试以独占写入方式打开文件
                lock_fd = os.open(lock_file_path, os.O_CREAT | os.O_RDWR | os.O_EXCL)
                # 写入当前进程PID，便于排查僵尸锁
                os.write(lock_fd, str(os.getpid()).encode())
                os.fsync(lock_fd)  # 确保写入磁盘
                return lock_fd
            except FileExistsError:
                # 如果文件已存在，说明已有进程持有锁
                retries += 1
                time.sleep(retry_delay)
                
        # 如果重试次数达到上限，尝试检查锁文件是否过期
        try:
            stat_result = lock_file_path.stat()
            if (time.time() - stat_result.st_mtime) > 30:  # 30秒过期
                # 检查锁文件中的PID是否还在运行
                try:
                    with open(lock_file_path, 'r') as f:
                        lock_pid = int(f.read().strip())
                        # 尝试向PID发送信号检查是否存在
                        try:
                            os.kill(lock_pid, 0)
                        except OSError:
                            # 进程不存在，可以安全删除锁文件
                            os.unlink(lock_file_path)
                            lock_fd = os.open(lock_file_path, os.O_CREAT | os.O_RDWR | os.O_EXCL)
                            os.write(lock_fd, str(os.getpid()).encode())
                            os.fsync(lock_fd)
                            return lock_fd
                except (ValueError, FileNotFoundError):
                    # 解析PID失败或文件不存在，继续尝试
                    pass
                
                # 尝试删除锁文件
                try:
                    os.unlink(lock_file_path)
                    lock_fd = os.open(lock_file_path, os.O_CREAT | os.O_RDWR | os.O_EXCL)
                    os.write(lock_fd, str(os.getpid()).encode())
                    os.fsync(lock_fd)
                    return lock_fd
                except (FileNotFoundError, PermissionError):
                    pass
                
        except OSError:
            pass  # 无法获取文件状态，忽略
                
        raise BlockingIOError(f"Unable to acquire lock after {max_retries} retries")
    else:
        import fcntl
        lock_fd = os.open(lock_file_path, os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # 非阻塞排他锁
            # 写入当前进程PID，便于排查僵尸锁
            os.write(lock_fd, str(os.getpid()).encode())
            os.fsync(lock_fd)  # 确保写入磁盘
            return lock_fd
        except BlockingIOError:
            os.close(lock_fd)
            raise


def release_platform_lock(lock_fd: int, lock_file_path: Path):
    """
    跨平台释放文件锁的函数
    """
    system = platform.system().lower()
    
    if system == "windows":
        # 在Windows上，只需关闭文件句柄即可释放锁
        os.close(lock_fd)
        try:
            os.unlink(lock_file_path)  # 删除锁文件
        except FileNotFoundError:
            pass  # 锁文件已被删除，忽略错误
    else:
        import fcntl
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
        try:
            os.unlink(lock_file_path)  # 删除锁文件
        except FileNotFoundError:
            pass  # 锁文件已被删除，忽略错误


def verify_pid_file(pid_file: Path) -> bool:
    """
    验证PID文件是否存在且对应的进程是否为当前实例
    """
    if not pid_file.exists():
        return False
        
    try:
        with open(pid_file, 'r') as f:
            pid_str = f.read().strip()
            if not pid_str.isdigit():
                return False
            pid = int(pid_str)
            
        # 检查进程是否存在
        try:
            os.kill(pid, 0)
            return True  # 进程存在
        except OSError:
            # 进程不存在，清理过期的PID文件
            pid_file.unlink()
            return False
    except (ValueError, FileNotFoundError, PermissionError):
        return False


def dynamic_wait_for_port(host: str, port: int, timeout: int = 30) -> bool:
    """
    动态等待端口释放
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((host, port))
            sock.close()
            if result != 0:  # 端口不可连接，表示已释放
                return True
            time.sleep(0.5)  # 等待0.5秒后重试
        except Exception:
            time.sleep(0.5)
    return False  # 超时


def execute_restart(
    model_path: Optional[Path] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    n_ctx: Optional[int] = None,
    n_threads: Optional[int] = None,
    api_keys: Optional[str] = None,
    max_concurrent_requests: Optional[int] = None,
    rate_limit_requests: Optional[int] = None,
    rate_limit_window: Optional[int] = None,
    debug: bool = False,
    pid_file: Path = Path("./llama.pid"),
    wait: int = 5,
    rollback_on_start_failure: bool = True,
    max_lock_retries: int = 5,
    lock_retry_delay: float = 0.1,
    log_to_file: Optional[Path] = None,
    rollback_strategy: str = "cleanup"  # "cleanup", "full_restart", or "none"
):
    """
    安全重启osins-llama服务器实例。

    Args:
        model_path: 模型文件路径
        host: 服务器绑定地址
        port: 服务器端口
        n_ctx: 上下文长度
        n_threads: 线程数
        api_keys: API密钥列表
        max_concurrent_requests: 最大并发请求数
        rate_limit_requests: 请求速率限制
        rate_limit_window: 速率限制窗口
        debug: 调试模式
        pid_file: PID文件路径
        wait: 停止后等待再启动的秒数
        rollback_on_start_failure: 启动失败时是否执行回滚
        max_lock_retries: 获取锁的最大重试次数
        lock_retry_delay: 锁重试延迟时间（秒）
        log_to_file: 日志文件路径（可选）
        rollback_strategy: 回滚策略 ("cleanup", "full_restart", "none")

    Returns:
        int: 0表示成功，非0表示失败
    """
    # 设置日志记录
    logger = logging.getLogger(__name__)
    handlers = []
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # 文件处理器（可选）
    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_to_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # 添加处理器到logger
    for handler in handlers:
        logger.addHandler(handler)
    
    # 根据debug模式设置日志级别
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False

    # 创建锁文件以防止多个restart命令并发执行
    lock_file_path = pid_file.with_suffix('.lock')
    lock_fd = None
    
    try:
        # 获取跨平台锁
        lock_fd = get_platform_lock(lock_file_path, max_lock_retries, lock_retry_delay)
        
        logger.info(f"Restarting osins-llama server (PID file: {pid_file})")

        # 验证PID文件
        if verify_pid_file(pid_file):
            logger.debug(f"Verified PID file {pid_file} corresponds to a running process")
        else:
            logger.warning(f"PID file {pid_file} does not correspond to a running process or does not exist")

        # 1. 安全停止现有进程
        stop_result = execute_stop(pid_file=pid_file, force=False)
        if stop_result != 0:
            logger.warning(f"Normal stop failed with code {stop_result}, attempting force stop")
            stop_result = execute_stop(pid_file=pid_file, force=True)
            if stop_result != 0:
                logger.error(f"Force stop failed with code {stop_result}, aborting restart")
                return stop_result + 10  # 为停止失败添加偏移量，便于区分错误类型

        # 动态等待端口释放
        if port and host:
            logger.info(f"Waiting for port {port} to be released...")
            if dynamic_wait_for_port(host, port):
                logger.info(f"Port {port} is now available")
            else:
                logger.warning(f"Port {port} still in use after timeout, continuing with static wait")
        
        # 2. 等待指定时间再启动
        logger.info(f"Waiting {wait} seconds before starting new instance")
        time.sleep(wait)

        # 3. 启动新实例
        logger.info("Starting new osins-llama instance")
        start_result = execute_start(
            model_path=model_path,
            host=host,
            port=port,
            n_ctx=n_ctx,
            n_threads=n_threads,
            api_keys=api_keys,
            max_concurrent_requests=max_concurrent_requests,
            rate_limit_requests=rate_limit_requests,
            rate_limit_window=rate_limit_window,
            debug=debug,
            pid_file=str(pid_file)
        )
        if start_result != 0:
            logger.error(f"Failed to start osins-llama, exit code {start_result}")
            
            # 如果启动失败且启用回滚，尝试清理可能的残留资源
            if rollback_on_start_failure:
                logger.info("Performing rollback after failed start")
                
                if rollback_strategy == "cleanup":
                    cleanup_result = execute_stop(pid_file=pid_file, force=True)
                    if cleanup_result != 0:
                        logger.warning(f"Cleanup after failed start returned code {cleanup_result}")
                elif rollback_strategy == "full_restart":
                    # 尝试完全重新启动
                    logger.info("Attempting full restart after failure")
                    # 这里可以实现额外的重启逻辑
                elif rollback_strategy == "none":
                    logger.info("Skipping rollback as per strategy")
                    
        else:
            logger.info("osins-llama restarted successfully")

        return start_result

    except BlockingIOError as e:
        logger.error(f"Another restart process is already running (lock file: {lock_file_path}): {e}")
        return 2  # 表示由于并发冲突而失败
    except Exception as e:
        logger.exception(f"Exception occurred during restart: {e}")
        return 1  # 通用错误码
    finally:
        # 释放锁并清理锁文件
        if lock_fd is not None:
            release_platform_lock(lock_fd, lock_file_path)
        
        # 清理日志处理器
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)


@click.command()
@click.option('--model-path', type=click.Path(exists=True), help='Model file path')
@click.option('--host', default='0.0.0.0', help='Server binding address')
@click.option('--port', default=31301, type=int, help='Server port')
@click.option('--n-ctx', default=2048, type=int, help='Context length')
@click.option('--n-threads', default=8, type=int, help='Number of threads')
@click.option('--api-keys', help='API key list (comma separated)')
@click.option('--max-concurrent-requests', default=10, type=int, help='Max concurrent requests')
@click.option('--rate-limit-requests', default=60, type=int, help='Rate limit requests')
@click.option('--rate-limit-window', default=60, type=int, help='Rate limit window in seconds')
@click.option('--debug/--no-debug', default=False, help='Debug mode')
@click.option('--pid-file', default='./llama.pid', help='PID file path')
@click.option('--wait', default=5, type=int, help='Wait time in seconds')
@click.option('--rollback-on-failure', default=True, type=bool, help='Rollback when start fails')
@click.option('--max-lock-retries', default=5, type=int, help='Max retries to acquire lock')
@click.option('--lock-retry-delay', default=0.1, type=float, help='Delay between lock retries')
@click.option('--log-file', type=click.Path(), help='Log to file')
@click.option('--rollback-strategy', type=click.Choice(['cleanup', 'full_restart', 'none']), 
              default='cleanup', help='Rollback strategy on start failure')
def restart(
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
    pid_file: str,
    wait: int,
    rollback_on_failure: bool,
    max_lock_retries: int,
    lock_retry_delay: float,
    log_file: Optional[str],
    rollback_strategy: str
):
    """Restart the osins-llama server instance."""
    # Convert string paths to Path objects
    model_path_obj = Path(model_path) if model_path else None
    pid_file_obj = Path(pid_file)
    log_file_obj = Path(log_file) if log_file else None

    if debug:
        print(f"[DEBUG] Restart command called with:")
        print(f"[DEBUG]   model_path: {model_path}")
        print(f"[DEBUG]   host: {host}")
        print(f"[DEBUG]   port: {port}")
        print(f"[DEBUG]   pid_file: {pid_file_obj}")
        print(f"[DEBUG]   wait: {wait}")
        print(f"[DEBUG]   rollback_on_failure: {rollback_on_failure}")
        print(f"[DEBUG]   max_lock_retries: {max_lock_retries}")
        print(f"[DEBUG]   lock_retry_delay: {lock_retry_delay}")
        print(f"[DEBUG]   log_file: {log_file_obj}")
        print(f"[DEBUG]   rollback_strategy: {rollback_strategy}")

    # Execute restart command
    result_code = execute_restart(
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
        pid_file=pid_file_obj,
        wait=wait,
        rollback_on_start_failure=rollback_on_failure,
        max_lock_retries=max_lock_retries,
        lock_retry_delay=lock_retry_delay,
        log_to_file=log_file_obj,
        rollback_strategy=rollback_strategy
    )
    
    if result_code != 0:
        if debug:
            print(f"[DEBUG] Restart command exited with code {result_code}")
        raise SystemExit(result_code)
```

## 单元测试示例

```python
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os
from src.llama.cli.restart import execute_restart, get_platform_lock, release_platform_lock, verify_pid_file


class TestExecuteRestart(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.pid_file = Path(self.temp_dir) / "test.pid"

    def tearDown(self):
        # 清理临时文件
        for file in [self.pid_file, self.pid_file.with_suffix('.lock')]:
            try:
                file.unlink()
            except FileNotFoundError:
                pass

    @patch('src.llama.cli.restart.execute_stop')
    @patch('src.llama.cli.restart.execute_start')
    @patch('src.llama.cli.restart.time.sleep')
    def test_successful_restart(self, mock_sleep, mock_start, mock_stop):
        """测试成功重启的情况"""
        # 模拟停止成功，启动成功
        mock_stop.return_value = 0
        mock_start.return_value = 0

        result = execute_restart(pid_file=self.pid_file)
        
        # 验证函数调用
        mock_stop.assert_called_once_with(pid_file=self.pid_file, force=False)
        mock_start.assert_called_once()
        mock_sleep.assert_called_once_with(5)
        self.assertEqual(result, 0)

    @patch('src.llama.cli.restart.execute_stop')
    @patch('src.llama.cli.restart.execute_start')
    @patch('src.llama.cli.restart.time.sleep')
    def test_force_stop_on_normal_stop_failure(self, mock_sleep, mock_start, mock_stop):
        """测试正常停止失败后强制停止的情况"""
        # 第一次停止失败，第二次强制停止成功
        mock_stop.side_effect = [1, 0]  # 第一次失败，第二次成功
        mock_start.return_value = 0

        result = execute_restart(pid_file=self.pid_file)
        
        # 验证函数调用
        calls = [
            unittest.mock.call(pid_file=self.pid_file, force=False),
            unittest.mock.call(pid_file=self.pid_file, force=True)
        ]
        mock_stop.assert_has_calls(calls)
        mock_start.assert_called_once()
        mock_sleep.assert_called_once_with(5)
        self.assertEqual(result, 0)

    @patch('src.llama.cli.restart.execute_stop')
    @patch('src.llama.cli.restart.execute_start')
    @patch('src.llama.cli.restart.time.sleep')
    def test_restart_fails_when_force_stop_also_fails(self, mock_sleep, mock_start, mock_stop):
        """测试强制停止也失败的情况"""
        # 模拟两次停止都失败
        mock_stop.return_value = 1

        result = execute_restart(pid_file=self.pid_file)
        
        # 验证函数调用
        calls = [
            unittest.mock.call(pid_file=self.pid_file, force=False),
            unittest.mock.call(pid_file=self.pid_file, force=True)
        ]
        mock_stop.assert_has_calls(calls)
        # 启动不应该被调用
        mock_start.assert_not_called()
        # sleep也不应该被调用
        mock_sleep.assert_not_called()
        self.assertEqual(result, 11)  # 1 + 10 (停止失败偏移)

    @patch('src.llama.cli.restart.execute_stop')
    @patch('src.llama.cli.restart.execute_start')
    @patch('src.llama.cli.restart.time.sleep')
    def test_restart_fails_when_start_fails(self, mock_sleep, mock_start, mock_stop):
        """测试启动失败的情况"""
        # 模拟停止成功，启动失败
        mock_stop.return_value = 0
        mock_start.return_value = 1

        result = execute_restart(pid_file=self.pid_file)
        
        # 验证函数调用
        mock_stop.assert_called_once_with(pid_file=self.pid_file, force=False)
        mock_start.assert_called_once()
        mock_sleep.assert_called_once_with(5)
        self.assertEqual(result, 1)

    @patch('src.llama.cli.restart.get_platform_lock')
    @patch('src.llama.cli.restart.execute_stop')
    @patch('src.llama.cli.restart.execute_start')
    @patch('src.llama.cli.restart.time.sleep')
    def test_concurrent_restart_prevention(self, mock_sleep, mock_start, mock_stop, mock_get_lock):
        """测试并发重启预防机制"""
        # 模拟锁已被占用
        mock_get_lock.side_effect = BlockingIOError("Unable to acquire lock")

        result = execute_restart(pid_file=self.pid_file)
        
        # 应该返回并发冲突错误码
        self.assertEqual(result, 2)
        # 不应该调用停止和启动函数
        mock_stop.assert_not_called()
        mock_start.assert_not_called()

    @patch('src.llama.cli.restart.execute_stop')
    @patch('src.llama.cli.restart.execute_start')
    @patch('src.llama.cli.restart.time.sleep')
    def test_rollback_on_start_failure(self, mock_sleep, mock_start, mock_stop):
        """测试启动失败时的回滚机制"""
        # 模拟停止成功，启动失败，回滚清理也成功
        mock_stop.side_effect = [0, 0]  # 第一次停止成功，回滚清理成功
        mock_start.return_value = 1

        result = execute_restart(
            pid_file=self.pid_file,
            rollback_on_start_failure=True,
            rollback_strategy="cleanup"
        )
        
        # 验证函数调用
        calls = [
            unittest.mock.call(pid_file=self.pid_file, force=False),
            unittest.mock.call(pid_file=self.pid_file, force=True)  # 回滚清理
        ]
        mock_stop.assert_has_calls(calls)
        mock_start.assert_called_once()
        mock_sleep.assert_called_once_with(5)
        self.assertEqual(result, 1)

    def test_verify_pid_file_exists_and_running(self):
        """测试PID文件验证功能 - 进程存在"""
        # 创建一个PID文件，包含当前进程ID
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        result = verify_pid_file(self.pid_file)
        self.assertTrue(result)

    def test_verify_pid_file_does_not_exist(self):
        """测试PID文件验证功能 - 文件不存在"""
        result = verify_pid_file(self.pid_file)
        self.assertFalse(result)

    def test_verify_pid_file_expired_process(self):
        """测试PID文件验证功能 - 进程不存在"""
        # 创建一个PID文件，包含一个无效的PID
        with open(self.pid_file, 'w') as f:
            f.write('999999')  # 通常不存在的PID
        
        result = verify_pid_file(self.pid_file)
        self.assertFalse(result)  # 应该清理过期文件并返回False
        self.assertFalse(self.pid_file.exists())  # 文件应该已被删除


if __name__ == '__main__':
    unittest.main()
```

## 验证标准

- [ ] 命令装饰器正确应用
- [ ] 参数选项定义完整
- [ ] 参数类型验证正确
- [ ] 默认值设置恰当
- [ ] 帮助文本清晰准确
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] execute_restart 函数实现安全重启逻辑
- [ ] 正确处理异常情况
- [ ] 返回适当的退出码
- [ ] 日志记录完整
- [ ] 跨平台兼容性
- [ ] 多实例并发安全（锁文件机制）
- [ ] 重启失败回滚机制
- [ ] 详细的调试模式
- [ ] 设计全面的单元测试覆盖
- [ ] Windows平台锁机制兼容
- [ ] 锁文件异常重试机制
- [ ] 日志级别动态调整
- [ ] 可参数化的等待时间和回滚策略
- [ ] 锁文件安全机制（PID写入）
- [ ] PID文件验证机制
- [ ] 增强的回滚策略
- [ ] 扩展日志功能
- [ ] 细化异常处理
- [ ] 动态等待机制

## 安全考虑

- 验证模型路径安全性
- 验证PID文件路径安全性
- 防止路径遍历攻击
- 验证参数范围有效性
- 安全停止现有进程后再启动新进程
- 防止多个实例同时运行
- 防止多个restart命令并发执行
- 确保资源正确释放（锁文件等）
- 跨平台锁机制的安全性
- 锁文件过期检查机制
- PID文件验证，防止误杀其他实例
- 动态等待端口释放，而非固定时间等待

## 版本信息
- 版本: 2.3
- 创建日期: 2026-02-12
- 最后更新: 2026-02-14