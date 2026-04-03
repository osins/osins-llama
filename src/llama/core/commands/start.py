import click
import os
import subprocess
import sys
from pathlib import Path
import json
import socket
from llama.config.config import Config


@click.command()
@click.option('-p', '--port', default=31301, type=int, help='Port to run the server on')
@click.option('-H', '--host', default='0.0.0.0', help='Host to bind the server to') 
@click.option('-m', '--model', required=False, help='Path to the local model file (optional, if connecting to external llama.cpp server)')
@click.option('--n-ctx', default=32768, type=int, help='Context size for the model')
@click.option('--n-threads', default=8, type=int, help='Number of threads to use')
@click.option('--api-keys', default='', help='API key list (comma separated)')
def start(port, host, model, n_ctx, n_threads, api_keys):
    """Start the LLM service with OpenAI-compatible API. 
    Connects to existing local llama.cpp server or starts local llama.cpp if model path provided."""
    
    click.echo(f"Starting LLM service on {host}:{port}")
    
    # Parse API keys
    api_keys_list = [key.strip() for key in api_keys.split(",") if key.strip()] if api_keys else []

    try:
        # Construct config object
        config_dict = {
            'model': {
                'path': model or '',
                'n_ctx': n_ctx,
                'n_threads': n_threads,
                'verbose': False
            },
            'resources': {
                'max_prompt_tokens': 2048,
                'max_total_tokens': 4096,
                'max_batch_size': 1
            },
            'security': {
                'api_keys': api_keys_list,
                'rate_limit_requests': 60,
                'rate_limit_window': 60,
                'max_concurrent_requests': 10
            },
            'service': {
                'host': host,
                'port': port,
                'debug': False
            }
        }
        
        config = Config(**config_dict)

        # Store server info in a temporary file for other commands to access
        server_info = {
            'port': port,
            'host': host,
            'model': model or 'external',
            'pid': os.getpid(),  # This won't be accurate for the actual server process
            'n_ctx': n_ctx,
            'n_threads': n_threads,
            'api_keys': api_keys_list
        }

        with open('server_info.json', 'w') as f:
            json.dump(server_info, f)

        # Start the server (this is a blocking call)
        from llama.api.server import start_server
        start_server(config)

    except ImportError as e:
        click.echo(f"Error importing server module: {str(e)}")
        click.echo("Make sure all required packages are installed.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error starting LLM service: {str(e)}")
        sys.exit(1)

    click.echo(f"Starting LLM service on {host}:{port} with model {model_path}")

    # Parse API keys
    api_keys_list = [key.strip() for key in api_keys.split(",") if key.strip()] if api_keys else []

    try:
        # Construct config object
        config_dict = {
            'model': {
                'path': str(model_path),
                'n_ctx': n_ctx,
                'n_threads': n_threads,
                'verbose': False
            },
            'resources': {
                'max_prompt_tokens': 2048,
                'max_total_tokens': 4096,
                'max_batch_size': 1
            },
            'security': {
                'api_keys': api_keys_list,
                'rate_limit_requests': 60,
                'rate_limit_window': 60,
                'max_concurrent_requests': 10
            },
            'service': {
                'host': host,
                'port': port,
                'debug': False
            }
        }
        
        config = Config(**config_dict)

        # Store server info in a temporary file for other commands to access
        server_info = {
            'port': port,
            'host': host,
            'model': str(model_path.absolute()),
            'pid': os.getpid(),  # This won't be accurate for the actual server process
            'n_ctx': n_ctx,
            'n_threads': n_threads,
            'api_keys': api_keys_list
        }

        with open('server_info.json', 'w') as f:
            json.dump(server_info, f)

        # Start the server (this is a blocking call)
        from llama.api.server import start_server
        start_server(config)

    except ImportError as e:
        click.echo(f"Error importing server module: {str(e)}")
        click.echo("Make sure all required packages are installed.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error starting LLM service: {str(e)}")
        sys.exit(1)