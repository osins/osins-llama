"""Start command for osins-llama server."""
import click
import errno
import os
import re
import stat
import ipaddress
import sys
from pathlib import Path
from typing import Optional, List

from ..config.config_manager import ConfigManager
from .process import ProcessManager


def validate_host(ctx, param, value):
    """验证主机地址格式"""
    try:
        # 尝试解析为IP地址
        ipaddress.ip_address(value)
        return value
    except ValueError:
        # 如果不是IP地址，只验证格式，不在CLI阶段解析域名
        # 更严格的主机名验证：只允许字母、数字、连字符和点，且不能以连字符或点开头或结尾
        host_pattern = r'^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]))*$'
        if not re.match(host_pattern, value):
            raise click.BadParameter(
                f"'{value}' is not a valid IP address or hostname format."
            )
        return value


def parse_api_keys(value: Optional[str]) -> Optional[List[str]]:
    """解析并验证API密钥列表"""
    if not value:
        return None
    keys = [k.strip() for k in value.split(',') if k.strip()]
    if not keys:
        raise click.BadParameter("API keys cannot be empty.")

    # 使用正则表达式验证API密钥格式
    pattern = re.compile(r'^[A-Za-z0-9_\-]{16,128}$')
    for key in keys:
        if not pattern.match(key):
            raise click.BadParameter(
                f"Invalid API key format: '{key}'. "
                f"Must be 16-128 alphanumeric characters, underscores, or hyphens."
            )

    # 有序去重
    seen = set()
    result = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


def secure_open_model(path: Path, max_model_size: int = None):
    """
    安全地打开模型文件，防止符号链接攻击和TOCTOU竞争条件

    Args:
        path: 模型文件路径
        max_model_size: 模型文件最大大小（字节），如果为None则从环境变量读取

    Returns:
        tuple: (file_descriptor, stat_result) - 调用方必须负责关闭fd

    Note:
        - 调用方必须负责关闭返回的文件描述符
        - 仅允许基于返回的fd进行模型读取
        - 禁止重新使用路径访问模型文件
    """
    # 从环境变量获取模型大小限制，如果未指定则使用默认值
    if max_model_size is None:
        env_value = os.environ.get('MAX_MODEL_SIZE')
        if env_value:
            try:
                max_model_size = int(env_value)
                if max_model_size <= 0:
                    raise ValueError
            except ValueError:
                raise click.BadParameter("Invalid MAX_MODEL_SIZE environment variable.")
        else:
            max_model_size = 10 * 1024 * 1024 * 1024  # 10GB default

    flags = os.O_RDONLY
    # O_NOFOLLOW and O_CLOEXEC are not available on Windows
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    if hasattr(os, 'O_CLOEXEC'):
        flags |= os.O_CLOEXEC

    fd = None
    try:
        fd = os.open(path, flags)

        st = os.fstat(fd)

        if not stat.S_ISREG(st.st_mode):
            raise click.BadParameter("Model file must be a regular file.")

        # Windows-specific handling for Unix-specific checks
        if sys.platform == 'win32':
            # On Windows, skip Unix-specific permission and ownership checks
            # since they don't translate well to Windows NTFS permissions
            pass
        else:
            # Unix-specific checks
            if st.st_uid != os.getuid():
                raise click.BadParameter("Model file must be owned by current user.")

            if st.st_mode & 0o022:  # Check if group/world writable
                raise click.BadParameter("Model file must not be group/world writable.")

            # Always enforce hard link count of 1 on Unix
            if st.st_nlink != 1:
                raise click.BadParameter("Model file must not have multiple hard links.")

        if st.st_size == 0:
            raise click.BadParameter("Model file is empty.")

        if st.st_size > max_model_size:
            raise click.BadParameter("Model file exceeds allowed size.")

        return fd, st

    except Exception:
        if fd is not None:
            os.close(fd)
        raise


def create_pid_file_secure(pid_file: Path):
    """安全地创建PID文件，使用原子操作防止符号链接攻击"""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    # O_NOFOLLOW is not available on Windows
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    fd = os.open(pid_file, flags, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode())
    finally:
        os.close(fd)


def validate_and_check_pid_file(pid_file: Path) -> None:
    """验证PID文件路径的安全性并检查是否有正在运行的进程"""
    if pid_file.exists():
        try:
            with open(pid_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if content:
                import json
                is_json = False
                port = None
                
                try:
                    data = json.loads(content)
                    is_json = True
                    port = data.get('port')
                except json.JSONDecodeError:
                    pass

                if is_json and port:
                    from src.llama.utils.pid_tools import find_pid_by_port
                    port_pid = find_pid_by_port(port)
                    
                    if port_pid:
                        raise click.BadParameter(
                            f"Server is already running on port {port} (PID: {port_pid}). "
                            f"Stop it first or use a different port."
                        )
                    else:
                        try:
                            pid_file.unlink()
                        except Exception as e:
                            click.echo(f"Warning: Failed to delete stale PID file {pid_file}: {e}", err=True)
                elif content.isdigit():
                    pid = int(content)
                    process_exists = False

                    try:
                        if sys.platform == 'win32':
                            import subprocess
                            result = subprocess.run(
                                ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV'],
                                capture_output=True,
                                text=True
                            )
                            process_exists = f'"{pid}"' in result.stdout
                        else:
                            os.kill(pid, 0)
                            process_exists = True
                    except Exception:
                        process_exists = False

                    if process_exists:
                        raise click.BadParameter(
                            f"Process with PID {pid} is already running. "
                            f"Check {pid_file}."
                        )
                    else:
                        try:
                            pid_file.unlink()
                        except Exception as e:
                            click.echo(f"Warning: Failed to delete stale PID file {pid_file}: {e}", err=True)
                else:
                    try:
                        pid_file.unlink()
                    except Exception as e:
                        click.echo(f"Warning: Failed to delete invalid PID file {pid_file}: {e}", err=True)
        except click.BadParameter:
            raise
        except Exception as e:
            click.echo(f"Warning: Failed to process PID file {pid_file}: {e}", err=True)

    # 确保PID文件路径不指向系统关键位置
    if pid_file.is_symlink():
        raise click.BadParameter("PID file path cannot be a symbolic link.")

    # 检查父目录是否存在且可写
    parent_dir = pid_file.parent
    if not parent_dir.exists():
        raise click.BadParameter(f"Parent directory does not exist: {parent_dir}")
    if not os.access(parent_dir, os.W_OK):
        raise click.BadParameter(f"Parent directory is not writable: {parent_dir}")

    # 使用 lstat 检查父目录的详细属性
    parent_stat = os.lstat(parent_dir)

    # 确认父目录确实是目录
    if not stat.S_ISDIR(parent_stat.st_mode):
        raise click.BadParameter(f"Parent path is not a directory: {parent_dir}")

    # 确认父目录不是符号链接
    if stat.S_ISLNK(parent_stat.st_mode):
        raise click.BadParameter(
            f"Parent directory cannot be a symbolic link: {parent_dir}"
        )

    # 检查父目录是否为world-writable
    is_world_writable = bool(parent_stat.st_mode & 0o002)
    if is_world_writable:
        # Windows-specific handling
        if sys.platform == 'win32':
            # On Windows, skip sticky bit and Unix ownership checks
            # since they don't apply directly to Windows permissions
            pass
        else:
            # Unix-specific checks
            has_sticky_bit = bool(parent_stat.st_mode & 0o1000)
            is_owned_by_user = parent_stat.st_uid == os.getuid()

            if not (has_sticky_bit or is_owned_by_user):
                raise click.BadParameter(
                    f"Parent directory {parent_dir} is world-writable but lacks sticky bit "
                    f"and is not owned by current user. This is unsafe."
                )


def safe_remove_pid(pid_file: Path):
    """安全地删除PID文件，防止TOCTOU竞态"""
    try:
        flags = os.O_RDONLY
        # O_NOFOLLOW is not available on Windows
        if hasattr(os, 'O_NOFOLLOW'):
            flags |= os.O_NOFOLLOW
        fd = os.open(pid_file, flags)
    except FileNotFoundError:
        return
    except OSError:
        return

    try:
        st_fd = os.fstat(fd)
        st_path = os.stat(pid_file, follow_symlinks=False)

        if st_fd.st_ino == st_path.st_ino:
            os.unlink(pid_file)
    finally:
        os.close(fd)


@click.command(context_settings=dict(help_option_names=['--help']))
@click.option(
    '-m', '--model', 'model_path',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True
    ),
    required=True,
    help='Path to model file'
)
@click.option(
    '-h', '--host',
    default='192.168.50.2',
    callback=validate_host,
    show_default=True,
    help='Server bind address'
)
@click.option(
    '-p', '--port',
    type=click.IntRange(1024, 65535),
    default=31301,
    show_default=True,
    help='Server port (1024-65535)'
)
@click.option(
    '-c', '--ctx-size', 'n_ctx',
    type=click.IntRange(128, 100000),
    default=8192,
    show_default=True,
    help='Context length (128-100000)'
)
@click.option(
    '-t', '--threads', 'n_threads',
    type=click.IntRange(1, 64),
    default=10,
    show_default=True,
    help='Number of threads (1-64)'
)
@click.option(
    '-ngl', '--gpu-layers', 'n_gpu_layers',
    type=click.IntRange(-1, 200),
    default=16,
    show_default=True,
    help='Number of GPU layers (-1 for all, 0 for CPU only)'
)
@click.option(
    '-b', '--batch-size', 'n_batch',
    type=click.IntRange(1, 4096),
    default=1024,
    show_default=True,
    help='Batch size for GPU (1-4096)'
)
@click.option(
    '-d', '--device',
    default='cuda0',
    show_default=True,
    help='GPU device to use (e.g., cuda0, cuda1)'
)
@click.option(
    '--kv-offload',
    is_flag=True,
    default=True,
    help='Enable KV cache offloading'
)
@click.option(
    '-fa', '--flash-attn',
    type=click.Choice(['auto', 'enabled', 'disabled']),
    default='auto',
    show_default=True,
    help='Flash attention mode'
)
@click.option(
    '--repack',
    is_flag=True,
    default=True,
    help='Enable model repacking'
)
@click.option(
    '--chat-template',
    default=None,
    help='Chat template string'
)
@click.option(
    '-v', '--verbose',
    is_flag=True,
    default=True,
    help='Enable verbose output'
)
@click.option(
    '-k', '--api-keys',
    callback=lambda ctx, param, value: parse_api_keys(value),
    help='API key list (comma separated, 16-128 chars each, '
         'alphanumeric, underscore, hyphen)'
)
@click.option(
    '--max-concurrent-requests',
    type=click.IntRange(1, 100),
    default=10,
    show_default=True,
    help='Max concurrent requests (1-100)'
)
@click.option(
    '--rate-limit-requests',
    type=click.IntRange(1, 10000),
    default=60,
    show_default=True,
    help='Rate limit requests per window (1-10000)'
)
@click.option(
    '--rate-limit-window',
    type=click.IntRange(1, 3600),
    default=60,
    show_default=True,
    help='Rate limit window in seconds (1-3600)'
)
@click.option(
    '--debug/--no-debug',
    default=False,
    help='Debug mode (WARNING: Do not use in production!)'
)
@click.option(
    '--pid-file',
    type=click.Path(resolve_path=True),
    default='./llama.pid',
    show_default=True,
    help='PID file path'
)
@click.pass_context
def start(
    ctx,
    model_path: Optional[str],
    host: str,
    port: int,
    n_ctx: int,
    n_threads: int,
    n_gpu_layers: int,
    n_batch: int,
    device: str,
    kv_offload: bool,
    flash_attn: str,
    repack: bool,
    chat_template: Optional[str],
    verbose: bool,
    api_keys: Optional[List[str]],
    max_concurrent_requests: int,
    rate_limit_requests: int,
    rate_limit_window: int,
    debug: bool,
    pid_file: str
):
    """Start the osins-llama server instance."""
    raw_model_path = Path(model_path)
    model_fd, model_stat = secure_open_model(raw_model_path)

    pid_file_obj = Path(pid_file).expanduser().absolute()

    validate_and_check_pid_file(pid_file_obj)

    cpu_limit = os.cpu_count() or 1
    if n_threads > cpu_limit:
        raise click.BadParameter(
            f"n_threads cannot exceed available CPU cores ({cpu_limit})."
        )

    try:
        cli_overrides = {
            "host": host,
            "port": port,
            "model_path": raw_model_path,
            "n_ctx": n_ctx,
            "n_threads": n_threads,
            "n_gpu_layers": n_gpu_layers,
            "n_batch": n_batch,
            "device": device,
            "kv_offload": kv_offload,
            "flash_attn": flash_attn,
            "repack": repack,
            "chat_template": chat_template,
            "verbose": verbose,
        }

        config_path = ctx.obj.config_path
        config_manager = ConfigManager(config_path)
        config = config_manager.load(cli_overrides=cli_overrides)

        from src.llama.utils.pid_tools import find_pid_by_port
        port_pid = find_pid_by_port(config.port)
        if port_pid:
            click.echo(f"Error: Port {config.port} is already in use by process with PID {port_pid}")
            click.echo("Please stop the existing process first or use a different port.")
            raise click.ClickException(f"Port {config.port} is already in use by process {port_pid}")

        process_manager = ProcessManager(
            expected_cmd_keyword="llama.api.server",
            stop_timeout=30
        )

        from .pid_file_manager import PidFileManager
        from ..models.pid_data import PidData

        pid_manager = PidFileManager()

        pid_data = PidData(
            model_path=str(config.model_path) if config.model_path else None,
            host=config.host,
            port=config.port,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            n_batch=n_batch,
            device=device,
            kv_offload=kv_offload,
            flash_attn=flash_attn,
            repack=repack,
            chat_template=chat_template,
            verbose=verbose,
            api_keys=','.join(api_keys) if api_keys else None,
            max_concurrent_requests=max_concurrent_requests,
            rate_limit_requests=rate_limit_requests,
            rate_limit_window=rate_limit_window,
            debug=debug
        )

        server_process = process_manager.start_detached(pid_data)
        click.echo(f"Server started successfully in guardian mode on {config.host}:{config.port}")
        click.echo(f"Server process PID: {server_process.pid}")
        click.echo("Server is now running independently in the background")

    except click.BadParameter as e:
        # 重新引发click特定异常
        safe_remove_pid(pid_file_obj)
        raise
    except Exception as exc:
        # 处理所有其他异常
        click.echo(f"Startup failed: {exc}", err=True)
        # 如果启动失败，安全清理PID文件
        safe_remove_pid(pid_file_obj)
        raise SystemExit(1)
    finally:
        # 确保关闭模型文件描述符
        try:
            os.close(model_fd)
        except OSError:
            # 如果文件描述符已经关闭，忽略错误
            pass