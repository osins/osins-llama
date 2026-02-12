"""Main CLI entry point for osins-llama."""
import click
from .start import start
from .stop import stop
from .restart import restart
from .status import status
from .config import config
from .logs import logs
from .health import health


@click.group()
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.option('--config', type=click.Path(exists=True), help='Specify configuration file path')
def main(verbose: bool, config: str):
    """CLI for managing osins-llama server."""
    if verbose:
        click.echo("Verbose mode enabled")


# Register all commands
main.add_command(start)
main.add_command(stop)
main.add_command(restart)
main.add_command(status)
main.add_command(config)
main.add_command(logs)
main.add_command(health)


if __name__ == '__main__':
    main()