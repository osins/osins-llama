"""Config command for osins-llama server."""
import click
import sys
from pathlib import Path

from .config import ConfigManager, ServerConfig


@click.group()
@click.pass_context
def config(ctx):
    """Manage server configuration."""
    pass


@config.command()
@click.option('--config-file', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def show(ctx, config_file: str):
    """Show current configuration."""
    try:
        config_path = Path(config_file) if config_file else None
        if not config_path:
            config_path = ctx.obj.get('config_path')
        
        config_manager = ConfigManager(config_path)
        config = config_manager.load()
        
        masked_config = ConfigManager.masked_dict(config)
        
        click.echo("Current configuration:")
        for key, value in masked_config.items():
            if value is not None:
                click.echo(f"  {key}: {value}")
        
    except Exception as e:
        click.echo(f"Failed to load configuration: {str(e)}", err=True)
        sys.exit(1)


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--config-file', type=click.Path(), help='Configuration file path')
@click.pass_context
def set(ctx, key: str, value: str, config_file: str):
    """Set a configuration value."""
    click.echo(f"Setting {key}={value}")
    # Note: Actual implementation would require updating the config file
    # This is a simplified version for demonstration
    click.echo("Configuration update functionality would be implemented here.")


@config.command()
@click.option('--config-file', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def reset(ctx, config_file: str):
    """Reset configuration to defaults."""
    click.echo("Resetting configuration to defaults.")
    # Note: Actual implementation would require resetting the config file
    # This is a simplified version for demonstration
    click.echo("Configuration reset functionality would be implemented here.")