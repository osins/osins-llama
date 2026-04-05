from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from .model_config import ModelConfig
from .resources_config import ResourcesConfig
from .security_config import SecurityConfig
from .service_config import ServiceConfig
from ..core.logger_manager import logger


class Config(BaseModel):
    model: ModelConfig
    resources: ResourcesConfig
    security: SecurityConfig
    service: ServiceConfig

    @classmethod
    def from_env(cls, model_path=None):
        import os

        # 从环境变量获取模型路径，但如果提供了参数，则使用参数值
        if model_path is None:
            model_path = os.getenv("LLAMA_MODEL_PATH", "")
            if not model_path or model_path.strip() == "":
                # 如果没有提供模型路径参数且环境变量也没有设置，则暂时不抛出错误
                # 让后续的命令行参数有机会覆盖
                model_path = ""
        else:
            # 如果提供了model_path参数，则使用它
            pass

        # 只有在最终没有提供模型路径时才抛出错误
        if not model_path or model_path.strip() == "":
            raise ValueError("Model path not provided. Please set LLAMA_MODEL_PATH environment variable.")

        # 验证模型路径是否存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # 获取API密钥，支持多种环境变量
        api_keys_raw = os.getenv("LLAMA_API_KEYS", "") or os.getenv("API_KEYS", "")
        api_keys = []
        if api_keys_raw:
            api_keys = [key.strip() for key in api_keys_raw.split(",") if key.strip()]

        # 如果没有设置API密钥，记录警告但不使用默认密钥（生产环境安全要求）
        if not api_keys:
            logger.warning("No API keys configured. This is insecure for production use.")

        return cls(
            model=ModelConfig(
                path=model_path,
                n_ctx=max(1, min(int(os.getenv("LLAMA_N_CTX", "32768")), 100000)),
                n_threads=max(1, min(int(os.getenv("LLAMA_N_THREADS", "10")), 64)),
                n_gpu_layers=max(-1, min(int(os.getenv("LLAMA_N_GPU_LAYERS", "16")), 200)),
                n_batch=max(1, min(int(os.getenv("LLAMA_N_BATCH", "1024")), 4096)),
                verbose=os.getenv("LLAMA_VERBOSE", "true").lower() == "true",
                device=os.getenv("LLAMA_DEVICE", "cuda0"),
                kv_offload=os.getenv("LLAMA_KV_OFFLOAD", "true").lower() == "true",
                flash_attn=os.getenv("LLAMA_FLASH_ATTN", "auto"),
                repack=os.getenv("LLAMA_REPACK", "true").lower() == "true",
                chat_template=os.getenv("LLAMA_CHAT_TEMPLATE", None)
            ),
            resources=ResourcesConfig(
                max_prompt_tokens=max(1, min(int(os.getenv("LLAMA_MAX_PROMPT_TOKENS", "16384")), 100000)),
                max_total_tokens=max(1, min(int(os.getenv("LLAMA_MAX_TOTAL_TOKENS", "32768")), 200000)),
                max_batch_size=max(1, min(int(os.getenv("LLAMA_MAX_BATCH_SIZE", "1")), 100))
            ),
            security=SecurityConfig(
                api_keys=api_keys,
                rate_limit_requests=max(1, int(os.getenv("LLAMA_RATE_LIMIT_REQUESTS", "60"))),
                rate_limit_window=max(1, int(os.getenv("LLAMA_RATE_LIMIT_WINDOW", "60"))),
                max_concurrent_requests=max(1, min(int(os.getenv("LLAMA_MAX_CONCURRENT_REQUESTS", "10")), 1000))
            ),
            service=ServiceConfig(
                host=os.getenv("LLAMA_HOST", "192.168.50.2"),
                port=max(1024, min(int(os.getenv("LLAMA_PORT", "31301")), 65535)),
                debug=os.getenv("LLAMA_DEBUG", "false").lower() == "true"
            )
        )


def validate_config_safety(config: Config):
    """
    验证配置的安全性
    """
    # 检查是否设置了API密钥
    if not config.security.api_keys:
        logger.warning("WARNING: No API keys are configured. Server is running without authentication.")
    
    # 检查调试模式
    if config.service.debug:
        logger.warning("WARNING: Debug mode is enabled. This may expose sensitive information.")
    
    # 检查并发限制
    if config.security.max_concurrent_requests > 100:
        logger.warning(f"WARNING: High concurrent request limit set: {config.security.max_concurrent_requests}. "
                      "Consider reducing for production use.")
    
    # 检查速率限制
    if config.security.rate_limit_requests > 1000:
        logger.info(f"INFO: High rate limit set: {config.security.rate_limit_requests}/min. "
                   "Ensure infrastructure can handle this load.")


def load_and_validate_config():
    """
    加载并验证配置
    """
    config = Config.from_env()
    validate_config_safety(config)
    return config