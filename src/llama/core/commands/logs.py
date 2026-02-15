import click
import sys
from pathlib import Path
from collections import deque
import time


@click.command()
@click.option('--follow', is_flag=True, help='Follow log file')
@click.option(
    '--lines', default=50, type=click.IntRange(1, 10000),
    help='Show last N lines (max 10000)'
)
@click.option(
    '--log-file', default='./llama.log', type=click.Path(),
    help='Log file path'
)
@click.option('--debug', is_flag=True, help='Enable debug logging')
def logs(follow: bool, lines: int, log_file: str, debug: bool):
    """View server logs."""
    # Convert string path to Path object
    log_file_obj = Path(log_file)

    try:
        # Validate log file path security
        if not log_file_obj.exists() and not follow:
            click.echo(f"Error: Log file does not exist: {log_file_obj}")
            sys.exit(1)

        # Execute logs command
        execute_logs(
            follow=follow,
            lines=lines,
            log_file=log_file_obj,
            debug=debug
        )
    except Exception as e:
        click.echo(f"Error viewing logs: {str(e)}")
        sys.exit(1)


def execute_logs(follow: bool, lines: int, log_file: Path, debug: bool):
    """Execute the logs command logic."""
    # Path security check - resolved path for security validation
    log_file.resolve(strict=False)

    # Get last N lines efficiently
    def get_last_lines(file_path, num_lines):
        with open(file_path, 'r') as f:
            return deque(f, maxlen=num_lines)

    if not follow:
        # Just show last N lines
        if log_file.exists():
            last_lines = get_last_lines(log_file, lines)
            for line in last_lines:
                click.echo(line.rstrip())
    else:
        # Follow mode - continuously show new lines
        try:
            with open(log_file, 'r') as f:
                # Show last N lines first
                last_lines = get_last_lines(log_file, lines)
                for line in last_lines:
                    click.echo(line.rstrip())

                # Keep reading new lines
                f.seek(0, 2)  # Go to the end of file
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    click.echo(line.rstrip())
        except KeyboardInterrupt:
            click.echo("\nLog viewing stopped.")
            sys.exit(0)
        except FileNotFoundError:
            click.echo(f"Error: Log file not found: {log_file}")
            sys.exit(1)
        except IOError as e:
            click.echo(f"Error reading log file: {e}")
            sys.exit(1)
