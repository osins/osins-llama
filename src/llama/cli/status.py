"""Status command for osins-llama server."""
import click
import requests
import sys
from pathlib import Path

from .process import ProcessManager
from .exceptions import ProcessError


@click.command()
@click.option('--pid-file', default='./llama.pid', help='PID file path')
@click.option('--api-url', default='http://localhost:31301', help='API endpoint URL')
@click.pass_context
def status(ctx, pid_file: str, api_url: str):
    """Check the status of osins-llama server."""
    try:
        process_manager = ProcessManager(
            pid_file=Path(pid_file),
            expected_cmd_keyword="llama.server",
            stop_timeout=30
        )
        
        # Check if process is running
        is_running = process_manager.is_running()
        
        if is_running:
            click.echo("✓ Server process is running")
            
            # Try to connect to the API endpoint
            try:
                response = requests.get(f"{api_url}/health", timeout=10)
                
                if response.status_code == 200:
                    click.echo("✓ API endpoint is accessible")
                    click.echo(f"  API URL: {api_url}")
                else:
                    click.echo("✗ API endpoint returned error")
                    click.echo(f"  Status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                click.echo("✗ API endpoint is not accessible")
                click.echo(f"  Error: {str(e)}")
        else:
            click.echo("✗ Server process is not running")
            sys.exit(1)
        
    except ProcessError as e:
        click.echo(f"Process error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Failed to check server status: {str(e)}", err=True)
        sys.exit(1)