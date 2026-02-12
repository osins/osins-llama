"""Restart command for osins-llama server."""
import click
import sys
import time
from pathlib import Path
from typing import Optional

from .process import ProcessManager
from .exceptions import ProcessError


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
            pid_file=Path(pid_file),
            expected_cmd_keyword="llama.server",
            stop_timeout=30
        )
        
        # Prepare command for restart
        cmd = [
            "python", "-m", "src.llama.server",
            "--host", host,
            "--port", str(port),
            "--n-ctx", str(n_ctx),
            "--n-threads", str(n_threads),
            "--max-concurrent-requests", str(max_concurrent_requests),
            "--rate-limit-requests", str(rate_limit_requests),
            "--rate-limit-window", str(rate_limit_window)
        ]
        
        if model_path:
            cmd.extend(["--model-path", model_path])
        
        if api_keys:
            cmd.extend(["--api-keys", api_keys])
        
        if debug:
            cmd.append("--debug")
        
        process_manager.restart(cmd)
        
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