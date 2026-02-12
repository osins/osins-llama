"""Logs command for osins-llama server."""
import click
import sys
import time
from pathlib import Path


@click.command()
@click.option('--follow', is_flag=True, help='Follow log file')
@click.option('--lines', default=50, type=int, help='Number of lines to show')
@click.option('--log-file', default='./llama.log', help='Log file path')
@click.pass_context
def logs(ctx, follow: bool, lines: int, log_file: str):
    """View server logs."""
    log_path = Path(log_file)
    
    if not log_path.exists():
        click.echo(f"Log file does not exist: {log_file}", err=True)
        sys.exit(1)
    
    # Show last N lines
    with open(log_path, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        
        # Get the last 'lines' lines
        last_lines = all_lines[-lines:] if len(all_lines) >= lines else all_lines
        
        for line in last_lines:
            click.echo(line.rstrip())
    
    # Follow mode
    if follow:
        click.echo("--- Following logs (Press Ctrl+C to stop) ---")
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                # Move to end of file
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        click.echo(line.rstrip())
                    else:
                        time.sleep(0.1)
        except KeyboardInterrupt:
            click.echo("\nStopped following logs.")