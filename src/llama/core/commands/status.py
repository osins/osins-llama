import click
import json
from pathlib import Path
import psutil
import requests
import socket


def is_port_open(host, port):
    """Check if a port is open on the given host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def is_process_running(pid):
    """Check if a process with the given PID is running."""
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except psutil.NoSuchProcess:
        return False
    except:
        return False


@click.command()
def status():
    """Show the current status of the LLM service."""
    server_info_path = Path('server_info.json')

    if not server_info_path.exists():
        click.echo("LLM service is not currently running.")
        return

    try:
        with open(server_info_path, 'r') as f:
            server_info = json.load(f)

        host = server_info.get('host', '0.0.0.0')
        port = server_info['port']
        pid = server_info.get('pid')
        model_name = Path(server_info['model']).name
        n_ctx = server_info.get('n_ctx', 'default')
        n_threads = server_info.get('n_threads', 'default')

        # Check if process is running
        process_running = False
        if pid:
            process_running = is_process_running(pid)

        # Check if port is accessible
        port_accessible = is_port_open('127.0.0.1', port)

        # Try to get API health status
        health_status = "unknown"
        try:
            response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                health_status = health_data.get('status', 'unknown')
        except:
            health_status = "unreachable"

        click.echo("LLM service status:")
        click.echo(f"  Status: {'RUNNING' if process_running and port_accessible else 'STOPPED'}")
        click.echo(f"  Health: {health_status}")
        click.echo(f"  Host: {host}")
        click.echo(f"  Port: {port}")
        click.echo(f"  Model: {model_name}")
        click.echo(f"  PID: {pid if pid else 'N/A'}")
        click.echo(f"  Context Size (n_ctx): {n_ctx}")
        click.echo(f"  Threads (n_threads): {n_threads}")
        click.echo(f"  Port Accessible: {'Yes' if port_accessible else 'No'}")
        click.echo(f"  Process Running: {'Yes' if process_running else 'No'}")

    except FileNotFoundError:
        click.echo("Could not find server information. Service may not be running.")
    except json.JSONDecodeError:
        click.echo("Server information file is corrupted.")
    except Exception as e:
        click.echo(f"Error checking LLM service status: {str(e)}")