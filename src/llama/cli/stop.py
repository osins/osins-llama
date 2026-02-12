"""Stop command for osins-llama server."""
import click
import sys
from pathlib import Path

from .process import ProcessManager
from .exceptions import ProcessNotRunning, PIDSecurityError, ProcessTimeout


@click.command()
@click.option('--pid-file', default='./llama.pid', help='PID file path')
@click.option('--force', is_flag=True, help='Force stop')
@click.pass_context
def stop(ctx, pid_file: str, force: bool):
    """Stop the osins-llama server."""
    try:
        process_manager = ProcessManager(
            pid_file=Path(pid_file),
            expected_cmd_keyword="llama.server",
            stop_timeout=30
        )
        
        process_manager.stop(force=force)
        
        click.echo("Server stopped successfully.")
        
    except ProcessNotRunning:
        click.echo("Server is not running.", err=True)
        sys.exit(1)
    except PIDSecurityError as e:
        click.echo(f"Security error: {e}", err=True)
        sys.exit(3)
    except ProcessTimeout:
        click.echo("Timeout waiting for server to stop.", err=True)
        sys.exit(4)
    except Exception as e:
        click.echo(f"Failed to stop server: {str(e)}", err=True)
        sys.exit(1)