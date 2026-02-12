import click
import json
import os
import signal
import psutil
from pathlib import Path


@click.command()
def restart():
    """Restart the LLM service."""
    server_info_path = Path('server_info.json')

    if not server_info_path.exists():
        click.echo("LLM service is not currently running.")
        # Just start the service if it's not running
        click.echo("Starting new LLM service...")
        click.echo("Please use the 'start' command to start the service with desired parameters.")
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
                click.echo(f"Previous LLM service (PID: {pid}) stopped successfully.")
            except psutil.NoSuchProcess:
                click.echo(f"Process with PID {pid} not found.")
            except psutil.TimeoutExpired:
                # Force kill if graceful termination fails
                process.kill()
                click.echo(f"Previous LLM service (PID: {pid}) forcefully stopped.")
            except psutil.AccessDenied:
                click.echo(f"Permission denied to stop process with PID {pid}.")
        else:
            click.echo(f"Stopping LLM service on port {server_info['port']}")

        # Remove the old server info file
        server_info_path.unlink()

        # Restart the service with the same parameters
        model_path = server_info['model']
        port = server_info['port']
        host = server_info.get('host', '0.0.0.0')
        n_ctx = server_info.get('n_ctx', 2048)
        n_threads = server_info.get('n_threads', 8)

        # Call the start command with the saved parameters
        from .start import start
        ctx = click.get_current_context()
        ctx.invoke(start, port=port, host=host, model=model_path, n_ctx=n_ctx, n_threads=n_threads)

        click.echo("LLM service restarted successfully.")

    except FileNotFoundError:
        click.echo("Could not find server information. Service may not be running.")
    except json.JSONDecodeError:
        click.echo("Server information file is corrupted.")
    except psutil.NoSuchProcess:
        click.echo("Service process not found. Attempting to start new service...")
        # Even if the old process wasn't found, try to start a new one
        if server_info_path.exists():
            server_info_path.unlink()
            
        # Start the service with the same parameters
        with open(server_info_path, 'r') as f:
            server_info = json.load(f)
        
        model_path = server_info['model']
        port = server_info['port']
        host = server_info.get('host', '0.0.0.0')
        n_ctx = server_info.get('n_ctx', 2048)
        n_threads = server_info.get('n_threads', 8)
        
        from .start import start
        ctx = click.get_current_context()
        ctx.invoke(start, port=port, host=host, model=model_path, n_ctx=n_ctx, n_threads=n_threads)
    except psutil.AccessDenied:
        click.echo("Permission denied when trying to restart the service.")
    except Exception as e:
        click.echo(f"Error restarting LLM service: {str(e)}")