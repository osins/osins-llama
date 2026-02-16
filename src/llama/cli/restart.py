"""Restart command for osins-llama server."""
import click
import sys
import time
from pathlib import Path
from typing import Optional

from .process import ProcessManager
from .exceptions import ProcessError
from .pid_file_manager import PidFileManager
from ..models.pid_data import PidData


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
@click.pass_context
def restart(
    ctx,
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
    wait: int
):
    """Restart the osins-llama server."""
    try:
        process_manager = ProcessManager(
            expected_cmd_keyword="llama.server",
            stop_timeout=30
        )

        # Stop the current process
        process_manager.stop()
        click.echo("Stopped the current server process.")
        
        # Wait a moment before restarting
        time.sleep(1)

        # Read the PID data to get the original startup parameters
        pid_manager = PidFileManager()
        pid_data = pid_manager.read(validate=True)
        
        if not pid_data:
            raise Exception("No saved data found in PID file, unable to restart")

        # Update the PID data with any command-line overrides
        if model_path:
            pid_data.model_path = model_path
        if host:
            pid_data.host = host
        if port:
            pid_data.port = port
        if n_ctx:
            pid_data.n_ctx = n_ctx
        if n_threads:
            pid_data.n_threads = n_threads
        if api_keys:
            pid_data.api_keys = api_keys
        if max_concurrent_requests:
            pid_data.max_concurrent_requests = max_concurrent_requests
        if rate_limit_requests:
            pid_data.rate_limit_requests = rate_limit_requests
        if rate_limit_window:
            pid_data.rate_limit_window = rate_limit_window
        if debug is not None:
            pid_data.debug = debug

        # 以守护模式重启进程
        process_manager.start_detached(pid_data=pid_data)
        click.echo(f"Server restarted successfully in guardian mode on {pid_data.host}:{pid_data.port}")

        # Wait for the server to restart
        click.echo(f"Waiting {wait} seconds for server to restart...")
        time.sleep(wait)

        click.echo("Server restarted successfully.")

    except ProcessError as e:
        click.echo(f"Process error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Failed to restart server: {str(e)}", err=True)
        sys.exit(1)