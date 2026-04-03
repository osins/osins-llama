import click
import json
import os
import signal
import psutil
import time
import socket
from pathlib import Path
from typing import Optional
from llama.core.logger_manager import logger


def get_platform_lock(lock_file_path: Path, max_retries: int = 5, retry_delay: float = 0.1):
    """
    跨平台获取文件锁的函数
    """
    system = os.name.lower()
    
    if system == "nt":  # Windows
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
    else:  # Unix-like systems
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
    system = os.name.lower()
    
    if system == "nt":  # Windows
        # 在Windows上，只需关闭文件句柄即可释放锁
        os.close(lock_fd)
        try:
            os.unlink(lock_file_path)  # 删除锁文件
        except FileNotFoundError:
            pass  # 锁文件已被删除，忽略错误
    else:  # Unix-like systems
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


def execute_stop(pid_file: Path = Path("./server_info.json"), force: bool = False) -> int:
    """
    停止LLM服务
    """
    if not pid_file.exists():
        logger.info("LLM service is not currently running.")
        return 0

    try:
        with open(pid_file, 'r') as f:
            server_info = json.load(f)

        pid = server_info.get('pid')
        
        if pid:
            try:
                process = psutil.Process(pid)
                # 尝试优雅终止
                if not force:
                    process.terminate()
                    # 等待进程结束
                    process.wait(timeout=10)
                    logger.info(f"LLM service (PID: {pid}) stopped successfully.")
                    return 0
                else:
                    process.kill()
                    logger.info(f"LLM service (PID: {pid}) forcefully stopped.")
                    return 0
            except psutil.NoSuchProcess:
                logger.info(f"Process with PID {pid} not found. Removing server information file.")
            except psutil.TimeoutExpired:
                if not force:
                    # 超时且未使用force，返回失败
                    logger.warning(f"LLM service (PID: {pid}) did not stop within timeout. Use force flag to kill.")
                    return 1
                else:
                    process.kill()
                    logger.info(f"LLM service (PID: {pid}) forcefully stopped after timeout.")
                    return 0
            except psutil.AccessDenied:
                logger.error(f"Permission denied to stop process with PID {pid}.")
                return 2
        else:
            logger.error("No PID found in server information.")
            return 3

        # 删除服务器信息文件
        pid_file.unlink()
        return 0

    except FileNotFoundError:
        logger.info("Could not find server information. Service may not be running.")
        return 0
    except json.JSONDecodeError:
        logger.error("Server information file is corrupted.")
        return 4
    except Exception as e:
        logger.exception(f"Error stopping LLM service: {str(e)}")
        return 5


@click.command()
@click.option('-p', '--port', default=31301, type=int, help='Port to run the server on')
@click.option('-H', '--host', default='0.0.0.0', help='Host to bind the server to')
@click.option('-m', '--model', help='Path to the model file (if not provided, uses existing instance parameters)')
@click.option('--n-ctx', default=2048, type=int, help='Context size for the model')
@click.option('--n-threads', default=8, type=int, help='Number of threads to use')
@click.option('--pid-file', default='./server_info.json', type=click.Path(), help='PID file path')
@click.option('--wait', default=5, type=int, help='Wait time in seconds before starting new instance')
@click.option('--rollback-on-failure', default=True, type=bool, help='Rollback when start fails')
@click.option('--max-lock-retries', default=5, type=int, help='Max retries to acquire lock')
@click.option('--lock-retry-delay', default=0.1, type=float, help='Delay between lock retries')
@click.option('--rollback-strategy', type=click.Choice(['cleanup', 'full_restart', 'none']), 
              default='cleanup', help='Rollback strategy on start failure')
@click.option('--debug/--no-debug', default=False, help='Debug mode')
def restart(
    port: int,
    host: str,
    model: Optional[str],
    n_ctx: int,
    n_threads: int,
    pid_file: str,
    wait: int,
    rollback_on_failure: bool,
    max_lock_retries: int,
    lock_retry_delay: float,
    rollback_strategy: str,
    debug: bool
):
    """Restart the LLM service with safe stop and start logic."""
    if debug:
        logger.debug("Debug mode enabled")
    
    pid_file_path = Path(pid_file)
    lock_file_path = pid_file_path.with_suffix('.lock')
    lock_fd = None
    
    try:
        # 获取跨平台锁
        lock_fd = get_platform_lock(lock_file_path, max_lock_retries, lock_retry_delay)
        
        logger.info(f"Restarting LLM service (PID file: {pid_file_path})")

        # 1. 安全停止现有进程
        logger.info("Stopping existing LLM service instance")
        stop_result = execute_stop(pid_file=pid_file_path, force=False)
        if stop_result != 0:
            logger.warning(f"Normal stop failed with code {stop_result}, attempting force stop")
            stop_result = execute_stop(pid_file=pid_file_path, force=True)
            if stop_result != 0:
                logger.error(f"Force stop failed with code {stop_result}, aborting restart")
                return stop_result + 10  # 为停止失败添加偏移量

        # 动态等待端口释放
        logger.info(f"Waiting for port {port} to be released...")
        if dynamic_wait_for_port(host, port):
            logger.info(f"Port {port} is now available")
        else:
            logger.warning(f"Port {port} still in use after timeout, continuing with static wait")
        
        # 等待指定时间再启动
        logger.info(f"Waiting {wait} seconds before starting new instance")
        time.sleep(wait)

        # 2. 启动新实例
        logger.info("Starting new LLM service instance")
        
        # 确定要使用的参数
        use_existing_params = False
        if not model and pid_file_path.exists():
            # 尝试使用现有参数
            try:
                with open(pid_file_path, 'r') as f:
                    existing_info = json.load(f)
                model = existing_info['model']
                port = existing_info.get('port', port)
                host = existing_info.get('host', host)
                n_ctx = existing_info.get('n_ctx', n_ctx)
                n_threads = existing_info.get('n_threads', n_threads)
                use_existing_params = True
                logger.info(f"Using existing parameters from {pid_file_path}")
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                logger.warning(f"Failed to read existing parameters from {pid_file_path}, using command line arguments")
        
        if not model:
            logger.error("Model path is required. Either provide --model option or ensure existing instance is running.")
            return 1
        
        model_path = Path(model)
        if not model_path.exists():
            logger.error(f"Model file does not exist: {model_path}")
            return 2
        
        # 调用start命令
        from .start import start
        ctx = click.get_current_context()
        
        try:
            ctx.invoke(start, port=port, host=host, model=model, n_ctx=n_ctx, n_threads=n_threads)
            logger.info("LLM service restarted successfully.")
            return 0
        except Exception as e:
            logger.error(f"Failed to start new LLM service instance: {str(e)}")
            
            # 如果启动失败且启用回滚，尝试清理
            if rollback_on_failure:
                logger.info(f"Performing rollback with strategy: {rollback_strategy}")
                if rollback_strategy == "cleanup":
                    cleanup_result = execute_stop(pid_file=pid_file_path, force=True)
                    if cleanup_result != 0:
                        logger.warning(f"Cleanup after failed start returned code {cleanup_result}")
                elif rollback_strategy == "full_restart":
                    logger.info("Full restart strategy not implemented yet")
                elif rollback_strategy == "none":
                    logger.info("Skipping rollback as per strategy")
            
            return 3

    except BlockingIOError as e:
        logger.error(f"Another restart process is already running (lock file: {lock_file_path}): {e}")
        return 4  # 表示由于并发冲突而失败
    except Exception as e:
        logger.exception(f"Exception occurred during restart: {e}")
        return 1  # 通用错误码
    finally:
        # 释放锁并清理锁文件
        if lock_fd is not None:
            release_platform_lock(lock_fd, lock_file_path)
        
        logger.debug("Restart command execution completed")