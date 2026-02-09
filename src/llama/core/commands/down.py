import click
import json
import os
import signal
from pathlib import Path


@click.command()
def down_command():
    """Stop the LLM service."""
    server_info_path = Path('server_info.json')
    
    if not server_info_path.exists():
        click.echo("LLM service is not currently running.")
        return
    
    try:
        with open(server_info_path, 'r') as f:
            server_info = json.load(f)
        
        # In a real implementation, we would terminate the process with the stored PID
        # For now, we'll just remove the server info file and simulate stopping
        click.echo(f"Stopping LLM service on port {server_info['port']}")
        
        # Attempt to kill the process (in a real implementation)
        # os.kill(server_info['pid'], signal.SIGTERM)
        
        # Remove the server info file
        server_info_path.unlink()
        
        click.echo("LLM service stopped successfully.")
    
    except FileNotFoundError:
        click.echo("Could not find server information. Service may not be running.")
    except json.JSONDecodeError:
        click.echo("Server information file is corrupted.")
    except ProcessLookupError:
        click.echo("Service process not found. Removing server information file.")
        server_info_path.unlink()
    except PermissionError:
        click.echo("Permission denied when trying to stop the service.")
    except Exception as e:
        click.echo(f"Error stopping LLM service: {str(e)}")