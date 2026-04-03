"""Updated model manager that interfaces with a native llama.cpp server instead of llama-cpp-python."""

from pathlib import Path
import threading
import time
import uuid
from llama.config.config import Config
import asyncio
from typing import AsyncGenerator, Optional

from .llamacpp_client import LlamaCppServer, LlamaCppClient


# ============================================================
# llama.cpp server API 支持的参数白名单
# 用于过滤无效参数
# ============================================================
LLAMA_CPP_VALID_PARAMS = {
    "prompt", "n_predict", "temperature", "top_k", "top_p", "min_p", "xtp", 
    "typical_p", "repeat_penalty", "repeat_last_n", "seed", "tfs_z", "mirostat", 
    "mirostat_tau", "mirostat_eta", "grammar", "logit_bias", "n_keep", 
    "ignore_eos", "stream", "n_probs", "min_keep", "penalize_nl", 
    "presence_penalty", "frequency_penalty", "dry_multiplier", "dry_base",
    "dry_allowed_length", "dry_penalty_last_n", "dry_sequence_breakers", 
    "skew", "xtc_probability", "xtc_threshold", "samplers", "speculative_n",
    "speculative_k", "speculative_alpha", "speculative_temperature"
}


def filter_llama_cpp_params(params: dict) -> dict:
    """
    过滤掉 llama.cpp 不支持的参数，只保留白名单中的参数。
    """
    # 同义参数映射
    alias_map = {
        "max_tokens": "n_predict",
        "max_new_tokens": "n_predict",
        "n_predict": "n_predict",
        "num_predict": "n_predict",
        "repetition_penalty": "repeat_penalty", 
        "rep_pen": "repeat_penalty",
        "stopping_strings": "stop",
        "mirostat": "mirostat",
        "tfs": "tfs_z",
    }
    
    # 将参数转换为llama.cpp参数名
    mapped = {}
    for key, value in params.items():
        if key == "max_tokens":
            mapped["n_predict"] = value
        else:
            target = alias_map.get(key, key)
            if target in mapped:
                # 处理多个同义词的情况
                if target in ["n_predict", "repeat_penalty"]:
                    mapped[target] = max(mapped[target], value)
                else:  # For stop, combine and deduplicate
                    existing = mapped[target] if isinstance(mapped[target], list) else [mapped[target]]
                    new_val = value if isinstance(value, list) else [value]
                    merged = list(dict.fromkeys(existing + new_val))
                    if len(merged) == 1 and merged[0] == '':
                        continue  # Skip empty string
                    mapped[target] = merged
            else:
                mapped[target] = value
                
    # 过滤支持的参数
    filtered = {k: v for k, v in mapped.items() if k in LLAMA_CPP_VALID_PARAMS}
    
    # 特殊字段处理
    if "stop" in filtered and not filtered["stop"]:
        del filtered["stop"]
    elif "stop" in filtered and isinstance(filtered["stop"], list):
        # Remove empty strings from stop sequence list
        filtered["stop"] = [s for s in filtered["stop"] if s]
        if not filtered["stop"]:
            del filtered["stop"]
    
    # Grammar must be either a string or not present
    if "grammar" in filtered and (not isinstance(filtered["grammar"], str) or not filtered["grammar"]):
        del filtered["grammar"]
        
    # Logit bias validation
    if "logit_bias" in filtered:
        lb = filtered["logit_bias"]
        if not lb:
            del filtered["logit_bias"]
        elif isinstance(lb, list) and len(lb) == 0:
            del filtered["logit_bias"]
    
    return filtered


class ModelManager:
    """
    模型管理器 - 更新版以使用本地llama.cpp服务器
    负责模型的加载、管理和生命周期控制
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self, config: Config = None):
        self.config = config or Config.from_env()
        self.model_path = self.config.model.path
        self.server: Optional[LlamaCppServer] = None
        self.client: Optional[LlamaCppClient] = None
        self._initialize_server()
    
    def _initialize_server(self):
        """初始化llama.cpp服务器进程和客户端。"""
        if not self.model_path:
            raise ValueError("Model path is not set")
                
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        print(f"Initializing llama.cpp server with model: {Path(self.model_path).name}")
        
        # 确定服务器端口（使用配置或默认值）
        port = getattr(self.config.service, 'port', 8080)
        host = getattr(self.config.service, 'host', '127.0.0.1')
        
        # 构建服务器参数
        server_kwargs = {
            'n_ctx': self.config.model.n_ctx,
            'n_threads': self.config.model.n_threads,
            'n_gpu_layers': self.config.model.n_gpu_layers,
            'n_batch': self.config.model.n_batch,
            'verbose': self.config.model.verbose,
        }
        
        # 创建并启动llama.cpp服务器
        self.server = LlamaCppServer(
            model_path=self.model_path,
            host=host,
            port=port,
            **{k: v for k, v in server_kwargs.items() if v is not None}
        )
        
        if not self.server.start():
            raise RuntimeError("Failed to start llama.cpp server")
        
        # 创建客户端连接到服务器
        self.client = LlamaCppClient(server_url=f"http://{host}:{port}")
        
        print(f"llama.cpp server initialized successfully: {Path(self.model_path).name}")
        print(f"Server endpoint: http://{host}:{port}")
    
    @classmethod
    def get_instance(cls, config: Config = None) -> "ModelManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance
    
    def get_model(self) -> Optional[LlamaCppClient]:
        return self.client
    
    def get_model_name(self) -> str:
        """Get the name of the loaded model.
        
        Returns:
            Model filename or empty string if no model loaded.
        """
        if not self.model_path:
            return ""
        return Path(self.model_path).name
    
    def reload_model(self, model_path: str = None):
        """重新加载模型 - 需要重启服务器进程"""
        if self.server:
            self.server.stop()
            
        if model_path:
            self.model_path = model_path
            self.config.model.path = model_path
            
        self._initialize_server()
    
    async def stream_generate(
        self,
        prompt: str,
        params: dict = None,
    ) -> AsyncGenerator[dict, None]:  # Changed to dict to match expected return type
        """
        异步流式生成（与llama.cpp服务器通信实现）。
        """
        from llama.core.logger_manager import logger
        
        if self.client is None:
            raise RuntimeError("Model is not loaded")
        
        raw_params = dict(params or {})
        raw_params["stream"] = True
        
        # 过滤和格式化参数以匹配llama.cpp API
        clean_params = filter_llama_cpp_params(raw_params)
        
        # 手动覆盖/添加确保使用正确的参数
        if "max_tokens" in raw_params:
            clean_params["n_predict"] = raw_params["max_tokens"]
        
        # 强制最大 token 上限保护（生产必须限制）
        max_tokens = clean_params.get("n_predict", 512)
        max_allowed = 4096
        clean_params["n_predict"] = min(int(max_tokens), max_allowed)
        
        logger.info(f"stream_generate clean_params keys: {list(clean_params.keys())}")
        
        # 转换参数名适配llama.cpp API
        params_for_api = clean_params.copy()
        if "max_tokens" in params_for_api:
            params_for_api["n_predict"] = params_for_api.pop("max_tokens")
        
        try:
            chunk_index = 0
            accumulated_text = ""
            
            for chunk_data in self.client.stream_completion(prompt, **params_for_api):
                # 处理llama.cpp服务器返回的数据
                text = chunk_data.get("content", "") if isinstance(chunk_data, dict) else str(chunk_data)
                
                if text:
                    accumulated_text += text
                    
                    # 生成符合 llama-cpp-python 之前的格式的响应    
                    chunk_id = f"cmpl-{uuid.uuid4().hex[:8]}"
                    model_filename = self.model_path.replace('\\', '/').split('/')[-1] if self.model_path else "unknown"
                    
                    # 格式化输出为兼容旧API的结构 - 模拟llama-cpp-python的返回格式
                    formatted_chunk = {
                        "choices": [{
                            "text": text,
                            "index": chunk_index,
                            "logprobs": None,
                            "finish_reason": None
                        }],
                        "created": int(time.time()),
                        "model": model_filename,
                        "object": "text_completion",
                        "id": chunk_id
                    }
                    
                    yield formatted_chunk
                    chunk_index += 1
                    logger.info(f"Generated token: {repr(text)}")
                    
                # 检查是否是停止标记
                if chunk_data.get("stop", False):
                    break
                    
        except Exception as e:
            logger.error(f"Streaming generation error: {e}", exc_info=True)
            raise

    async def generate(self, prompt: str, params: dict = None) -> dict:
        """同步生成（包装为异步接口）- 与llama.cpp服务器API兼容。"""
        from llama.core.logger_manager import logger
        
        if self.client is None:
            raise RuntimeError("Model is not loaded")
            
        raw_params = dict(params or {})
        raw_params["stream"] = False  # Non-streaming request
        
        # 过滤和格式化参数
        clean_params = filter_llama_cpp_params(raw_params)
        
        # 强制最大 token 上限保护
        max_tokens = clean_params.get("n_predict", 512)
        max_allowed = 4096
        clean_params["n_predict"] = min(int(max_tokens), max_allowed)
        
        # 确保参数键名正确
        params_for_api = clean_params.copy()
        if "max_tokens" in params_for_api:
            params_for_api["n_predict"] = params_for_api.pop("max_tokens")
        
        try:
            loop = asyncio.get_event_loop()
            # 在线程池中执行同步HTTP请求
            result = await loop.run_in_executor(
                None,
                lambda: self.client.completion(prompt, **params_for_api)
            )
            
            # 将llama.cpp响应转换为模拟之前的llama-cpp-python格式
            model_filename = self.model_path.replace('\\', '/').split('/')[-1] if self.model_path else "unknown"
            
            # 构建类似llama-cpp-python的结果格式
            choices = []
            content = result.get("content", "") if isinstance(result, dict) else str(result)
            
            if isinstance(result, dict):
                choices = [{
                    "text": content,
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "stop"
                }]
            else:
                choices = [{
                    "text": str(result),
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "stop"
                }]
            
            # 包装为llama-cpp-python兼容格式
            formatted_result = {
                "choices": choices,
                "created": int(time.time()),
                "model": model_filename,
                "object": "text_completion",
                "id": f"cmpl-{uuid.uuid4().hex[:8]}",
                "usage": {
                    "prompt_tokens": result.get("tokens_evaluated", 0),
                    "completion_tokens": result.get("tokens_predicted", len(content.split())),
                    "total_tokens": result.get("tokens_evaluated", 0) + result.get("tokens_predicted", len(content.split()))
                }
            }
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error in model non-stream generation: {e}", exc_info=True)  
            raise
        
    def shutdown(self) -> bool:
        """关闭模型服务器。"""
        if self.server:
            try:
                self.server.stop()
                return True
            except Exception:
                return False
        return True