import click
import json
from pathlib import Path


@click.command()
def status_command():
    """Show the current status of the LLM service."""
    server_info_path = Path('server_info.json')
    
    if not server_info_path.exists():
        click.echo("LLM service is not currently running.")
        return
    
    try:
        with open(server_info_path, 'r') as f:
            server_info = json.load(f)
        
        # In a real implementation, we would check if the process is actually running
        # For now, we'll just report the stored information
        click.echo("LLM service is running:")
        click.echo(f"  Port: {server_info['port']}")
        click.echo(f"  Model: {Path(server_info['model']).name}")
        click.echo(f"  PID: {server_info.get('pid', 'N/A')}")
    
    except FileNotFoundError:
        click.echo("Could not find server information. Service may not be running.")
    except json.JSONDecodeError:
        click.echo("Server information file is corrupted.")
    except Exception as e:
        click.echo(f"Error checking LLM service status: {str(e)}")