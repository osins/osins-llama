"""Health command for osins-llama server."""
import click
import requests
import sys
import re
from src.llama.core.logger_manager import logger


def validate_api_url(ctx, param, value):
    """Validate API URL format."""
    # Check if URL has http or https protocol
    if not re.match(r'^https?://', value):
        raise click.BadParameter(f"URL must use http or https protocol: {value}")

    # Check if URL has a valid hostname
    url_pattern = r'^https?://([a-zA-Z0-9.-]+)(:[0-9]+)?(/.*)?$'
    if not re.match(url_pattern, value):
        raise click.BadParameter(f"Invalid URL format: {value}")

    return value


def validate_timeout(ctx, param, value):
    """Validate timeout value is within range."""
    if value < 1 or value > 300:
        raise click.BadParameter(f"Timeout must be between 1 and 300 seconds: {value}")
    return value


@click.command()
@click.option(
    '--api-url',
    default='http://localhost:31301',
    help='Target API URL, protocol must be http or https',
    callback=validate_api_url
)
@click.option(
    '--timeout',
    default=30,
    type=int,
    help='Request timeout in seconds (1-300)',
    callback=validate_timeout
)
@click.pass_context
def health(ctx, api_url: str, timeout: int):
    """Perform health check on the server."""
    # Use the global logger instance
    pass
    
    try:
        logger.info(f"Performing health check on {api_url} with timeout {timeout}s")
        
        # Perform health check
        health_url = f"{api_url}/health"
        response = requests.get(health_url, timeout=timeout)
        
        if response.status_code == 200:
            logger.info(f"Server is healthy - {api_url}")
            click.echo("✓ Server is healthy")
            try:
                health_data = response.json()
                status = health_data.get('status', 'unknown')
                logger.debug(f"Health check status: {status}")
                click.echo(f"  Status: {status}")
                if 'version' in health_data:
                    version = health_data['version']
                    logger.debug(f"Server version: {version}")
                    click.echo(f"  Version: {version}")
            except ValueError:
                # Response is not JSON, just show the raw text
                logger.debug(f"Response is not JSON: {response.text[:100]}...")
                click.echo(f"  Response: {response.text[:100]}...")
            sys.exit(0)
        else:
            console_msg = f"✗ Server returned error: {response.status_code} - {api_url}"
            logger_msg = f"Server returned error: {response.status_code} - {api_url}"
            logger.error(logger_msg)
            click.echo(console_msg, err=True)
            sys.exit(1)
            
    except requests.exceptions.Timeout:
        console_msg = f"✗ Request timed out after {timeout} seconds - {api_url}"
        logger_msg = f"Request timed out after {timeout} seconds - {api_url}"
        logger.error(logger_msg)
        click.echo(console_msg, err=True)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        console_msg = f"✗ Cannot connect to server - {api_url}"
        logger_msg = f"Cannot connect to server - {api_url}"
        logger.error(logger_msg)
        click.echo(console_msg, err=True)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        console_msg = f"✗ Request failed: {str(e)} - {api_url}"
        logger_msg = f"Request failed: {str(e)} - {api_url}"
        logger.error(logger_msg)
        click.echo(console_msg, err=True)
        sys.exit(1)
    except Exception as e:
        console_msg = f"✗ Health check failed: {str(e)} - {api_url}"
        logger_msg = f"Health check failed: {str(e)} - {api_url}"
        logger.error(logger_msg)
        click.echo(console_msg, err=True)
        sys.exit(1)
    except click.BadParameter as e:
        console_msg = f"✗ Parameter validation failed: {str(e)}"
        logger_msg = f"Parameter validation failed: {str(e)}"
        logger.error(logger_msg)
        click.echo(console_msg, err=True)
        sys.exit(2)