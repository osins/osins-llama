"""Config command for osins-llama server."""
import json
import logging
import sys
from pathlib import Path
import click
from typing import Optional

from ..utils.security_utils import validate_config_path


CONFIG_FILE = Path("./llama_config.json")
logger = logging.getLogger("config")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def load_config(config_path: Path = None) -> dict:
    """加载配置文件，如果不存在则返回空字典"""
    config_file = config_path or CONFIG_FILE
    try:
        if config_file.exists():
            with config_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def save_config(config: dict, config_path: Path = None):
    """使用临时文件保存配置，避免写入中断导致配置文件损坏"""
    config_file = config_path or CONFIG_FILE
    
    # 进行路径安全校验，防止路径遍历攻击
    if '..' in str(config_file) or config_file.is_absolute() and not str(config_file).startswith(str(Path.cwd())):
        raise ValueError("Invalid config file path")
    
    try:
        # 创建临时文件
        temp_file = config_file.with_suffix(config_file.suffix + '.tmp')
        
        # 写入临时文件
        with temp_file.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        # 原子性地替换原文件
        temp_file.replace(config_file)
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        # 如果临时文件存在，清理它
        if temp_file.exists():
            temp_file.unlink()
        raise


@click.group()
def config():
    """Manage server configuration."""
    pass


@config.command()
@click.option('-f', '--config-file', type=click.Path(), default="./llama_config.json",
              help="Path to the configuration file")
def show(config_file: str):
    """Show current configuration."""
    execute_show(Path(config_file))


def execute_show(config_path: Path):
    """显示当前配置"""
    config = load_config(config_path)
    if not config:
        logger.info("Configuration is empty")
        click.echo("Configuration is empty")
    else:
        for key, value in config.items():
            click.echo(f"{key} = {value}")


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('-f', '--config-file', type=click.Path(), default="./llama_config.json",
              help="Path to the configuration file")
def set(key: str, value: str, config_file: str):
    """Set configuration item."""
    try:
        execute_set(key, value, Path(config_file))
    except Exception as e:
        click.echo(f"Failed to set configuration: {str(e)}", err=True)
        sys.exit(1)


def execute_set(key: str, value: str, config_path: Path):
    """设置配置项"""
    if not key or any(c in key for c in " \t\n\r/\\"):
        logger.error(f"Invalid config key: {key}")
        raise ValueError("Invalid config key")
    config = load_config(config_path)
    config[key] = value
    save_config(config, config_path)
    logger.info(f"Set configuration: {key} = {value}")
    click.echo(f"Successfully set {key} = {value}")


@config.command()
@click.option('-f', '--config-file', type=click.Path(), default="./llama_config.json",
              help="Path to the configuration file")
def reset(config_file: str):
    """Reset configuration."""
    try:
        execute_reset(Path(config_file))
    except Exception as e:
        click.echo(f"Failed to reset configuration: {str(e)}", err=True)
        sys.exit(1)


def execute_reset(config_path: Path):
    """重置配置"""
    if config_path.exists():
        try:
            config_path.unlink()
            logger.info("Configuration reset successfully")
            click.echo("Configuration reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
            raise
    else:
        logger.info("Configuration file does not exist, nothing to reset")
        click.echo("Configuration file does not exist, nothing to reset")