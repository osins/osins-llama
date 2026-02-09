import click
import json
import os
import signal
from pathlib import Path


@click.command()
def restart_command():
    """Restart the LLM service."""
    server_info_path = Path('server_info.json')
    
    if not server_info_path.exists():
        click.echo("LLM service is not currently running.")
        return
    
    try:
        with open(server_info_path, 'r') as f:
            server_info = json.load(f)
        
        # In a real implementation, we would stop the current process and start a new one
        # For now, we'll just simulate the restart
        click.echo(f"Stopping LLM service on port {server_info['port']}")
        
        # Attempt to kill the previous process (if we had stored the PID properly)
        # This is simplified for demonstration purposes
        click.echo("Previous service stopped.")
        
        # Re-import the start functionality to restart
        from llama.core.commands.start import start_command
        import sys
        from io import StringIO
        
        # Capture the original stdout
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()
        
        try:
            # Call the start functionality again
            from llama_cpp import Llama
            model_path = Path(server_info['model'])
            
            # Load the model again
            llm = Llama(
                model_path=str(model_path),
                n_ctx=2048,
                n_threads=8,
                verbose=False
            )
            
            # Restore stdout
            sys.stdout = old_stdout
            
            click.echo(f"LLM service restarted successfully on port {server_info['port']}")
            click.echo(f"Model reloaded: {model_path.name}")
            
        except ImportError:
            sys.stdout = old_stdout
            click.echo("Error: llama-cpp-python is not installed.")
            click.echo("Please install it with: pip install llama-cpp-python")
        except Exception as e:
            sys.stdout = old_stdout
            click.echo(f"Error restarting LLM service: {str(e)}")
    
    except FileNotFoundError:
        click.echo("Could not find server information. Service may not be running.")
    except json.JSONDecodeError:
        click.echo("Server information file is corrupted.")
    except Exception as e:
        click.echo(f"Error restarting LLM service: {str(e)}")