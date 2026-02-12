import click
import json
import os
import signal
import psutil
from pathlib import Path


@click.command()
def down():
    """Stop the LLM service."""
    server_info_path = Path('server_info.json')

    if not server_info_path.exists():
        click.echo("LLM service is not currently running.")
        return

    try:
        with open(server_info_path, 'r') as f:
            server_info = json.load(f)

        pid = server_info.get('pid')
        
        if pid:
            try:
                process = psutil.Process(pid)
                # Terminate the process gracefully
                process.terminate()
                # Wait for the process to finish
                process.wait(timeout=10)
                click.echo(f"LLM service (PID: {pid}) stopped successfully.")
            except psutil.NoSuchProcess:
                click.echo(f"Process with PID {pid} not found. Removing server information file.")
            except psutil.TimeoutExpired:
                # Force kill if graceful termination fails
                process.kill()
                click.echo(f"LLM service (PID: {pid}) forcefully stopped.")
            except psutil.AccessDenied:
                click.echo(f"Permission denied to stop process with PID {pid}.")
        else:
            click.echo(f"Stopping LLM service on port {server_info['port']}")

        # Remove the server info file
        server_info_path.unlink()

        click.echo("LLM service stopped successfully.")

    except FileNotFoundError:
        click.echo("Could not find server information. Service may not be running.")
    except json.JSONDecodeError:
        click.echo("Server information file is corrupted.")
    except psutil.NoSuchProcess:
        click.echo("Service process not found. Removing server information file.")
        if server_info_path.exists():
            server_info_path.unlink()
    except psutil.AccessDenied:
        click.echo("Permission denied when trying to stop the service.")
    except Exception as e:
        click.echo(f"Error stopping LLM service: {str(e)}")