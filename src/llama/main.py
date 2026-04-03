import click
from llama.core.commands.start import start
from llama.core.commands.restart import restart
from llama.core.commands.down import down
from llama.core.commands.status import status
from llama.core.commands.logs import logs


@click.group()
def cli():
    """Llama CLI - A tool for managing and running LLM models with OpenAI-compatible API."""
    pass


# 添加各个子命令
cli.add_command(start)
cli.add_command(restart)
cli.add_command(down)
cli.add_command(status)
cli.add_command(logs)


if __name__ == "__main__":
    cli()