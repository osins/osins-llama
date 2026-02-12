"""Health command for osins-llama server."""
import click
import requests
import sys


@click.command()
@click.option('--api-url', default='http://localhost:31301', help='API endpoint URL')
@click.option('--timeout', default=30, type=int, help='Timeout in seconds')
@click.pass_context
def health(ctx, api_url: str, timeout: int):
    """Perform health check on the server."""
    try:
        # Perform health check
        health_url = f"{api_url}/health"
        response = requests.get(health_url, timeout=timeout)
        
        if response.status_code == 200:
            click.echo("✓ Server is healthy")
            try:
                health_data = response.json()
                click.echo(f"  Status: {health_data.get('status', 'unknown')}")
                if 'version' in health_data:
                    click.echo(f"  Version: {health_data['version']}")
            except ValueError:
                # Response is not JSON, just show the raw text
                click.echo(f"  Response: {response.text[:100]}...")
        elif response.status_code == 404:
            click.echo("✗ Health check endpoint not found", err=True)
            sys.exit(1)
        else:
            click.echo(f"✗ Server returned error: {response.status_code}", err=True)
            sys.exit(1)
            
    except requests.exceptions.Timeout:
        click.echo(f"✗ Request timed out after {timeout} seconds", err=True)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        click.echo("✗ Cannot connect to server", err=True)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        click.echo(f"✗ Request failed: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Health check failed: {str(e)}", err=True)
        sys.exit(1)