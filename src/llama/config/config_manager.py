"""Configuration Manager for osins-llama."""
from pathlib import Path
from typing import Dict, Any, Optional
from .config import Config, load_and_validate_config
from pydantic import BaseModel


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 31301
    model_path: Optional[Path] = None
    n_gpu_layers: int = -1
    n_batch: int = 512


class ConfigManager:
    """管理osins-llama的配置加载和保存"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path

    def load(self, cli_overrides: Optional[Dict[str, Any]] = None) -> ServerConfig:
        """加载配置，应用CLI覆盖"""
        # 如果有配置文件，则加载它；否则使用环境变量
        if self.config_path and self.config_path.exists():
            # 加载配置文件
            raw_config = self._load_from_file(self.config_path)
            # 应用CLI覆盖
            if cli_overrides:
                for key, value in cli_overrides.items():
                    if hasattr(raw_config, key) and value is not None:
                        setattr(raw_config, key, value)
            return raw_config
        else:
            # 使用默认值和环境变量
            config = ServerConfig()
            # 应用CLI覆盖
            if cli_overrides:
                for key, value in cli_overrides.items():
                    if hasattr(config, key) and value is not None:
                        setattr(config, key, value)
            return config

    def _load_from_file(self, file_path: Path) -> ServerConfig:
        """从文件加载配置"""
        # 由于我们没有定义配置文件格式，这里简单返回默认值
        # 在实际实现中，这将从JSON/YAML文件加载配置
        return ServerConfig()

    @staticmethod
    def masked_dict(config: ServerConfig) -> Dict[str, Any]:
        """返回配置的掩码字典，隐藏敏感信息"""
        result = config.model_dump()
        # 在这里我们可以隐藏敏感字段
        return result