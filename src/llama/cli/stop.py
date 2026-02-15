"""Stop command for osins-llama server."""
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
    
    # 清理PID文件
    _cleanup_pid_file(pid_file, logger)
    
    return 0  # 成功停止
    


def _is_safe_path(path: Path) -> bool:
    """确保 PID 文件在预期目录下，防止路径遍历"""
    try:
        resolved = path.resolve(strict=False)
        allowed_dir = Path.cwd().resolve()
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


@click.command()
@click.option('--pid-file', default='./llama.pid', type=click.Path(), help='PID file path')
@click.option('--force', is_flag=True, help='Force stop')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def stop(pid_file: str, force: bool, verbose: bool):
    """Stop the running osins-llama server instance."""
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