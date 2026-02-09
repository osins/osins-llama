import click
from llama.core.commands.start import start_command
from llama.core.commands.restart import restart_command
from llama.core.commands.down import down_command
from llama.core.commands.status import status_command


@click.group()
def cli():
    """Llama CLI - A tool for managing and running LLM models with llama_cpp."""
    pass


# 添加各个子命令
cli.add_command(start_command)
cli.add_command(restart_command)
cli.add_command(down_command)
cli.add_command(status_command)


if __name__ == "__main__":
    cli()