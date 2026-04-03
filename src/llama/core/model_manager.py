"""Updated model manager that interfaces with a native llama.cpp server instead of llama-cpp-python."""

from pathlib import Path
import threading
import time
import uuid
from llama.config.config import Config
import asyncio
from typing import AsyncGenerator, Optional

from .llamacpp_client import LlamaCppClient
from .llama_model_client import LlamaModelClient


def filter_llama_params(params: dict) -> dict:
    """
    过滤掉 llama.cpp 不支持的参数，只保留白名单中的参数。

    SillyTavern 会发送大量 OpenAI 兼容参数（n, best_of, cache_prompt,
    samplers, dry_multiplier 等），llama.cpp server 只接受特定字段。
    此函数统一过滤，一劳永 pit一劳永逸。

    特殊处理：
      - grammar:   必须是有效语法或 None，空字符串 "" 会导致错误
      - stop:      去重、去空值后若为空列表则丢弃。
    """
    # 同义参数映射
    alias_map = {
        # 同义的 n_predict 字段，统一映射到 n_predict
        "max_tokens": "n_predict",
        "max_new_tokens": "n_predict",
        "n_predict": "n_predict",
        "num_predict": "n_predict",
        # 同义的 repeat_penalty 字段
        "repetition_penalty": "repeat_penalty",
        "rep_pen": "repeat_penalty",
        # 同义的 stop 字段（llama.cpp server expects "stop")
        "stopping_strings": "stop", 
        # 同义的 mirostat 字段
        "mirostat": "mirostat",
        # 同义的 tfs_z 字段
        "tfs": "tfs_z",
    }
    
    # 步骤1: 按别名映射表重命名字段
    mapped = {}
    for key, value in params.items():
        target = alias_map.get(key, key)
        
        if target in ["n_predict", "repeat_penalty"] and target in mapped:
            # 多个同义字段时取最大值
            mapped[target] = max(mapped[target], value)
        elif target == "stop" and "stop" in mapped:
            # 合并去重
            existing = mapped["stop"] if isinstance(mapped["stop"], list) else [mapped["stop"]]
            new_val = value if isinstance(value, list) else [value]
            merged = list(dict.fromkeys(existing + new_val))
            mapped["stop"] = merged
        else:
            mapped[target] = value
            
    # 步骤2: 通过白名单过滤
    whitelist = {
        "n_predict", "temperature", "top_k", "top_p", "min_p", "xtp", 
        "typical_p", "repeat_penalty", "repeat_last_n", "seed", "tfs_z", 
        "mirostat", "mirostat_tau", "mirostat_eta", "grammar", "logit_bias", 
        "n_keep", "ignore_eos", "stream", "n_probs", "min_keep", "penalize_nl", 
        "presence_penalty", "frequency_penalty", "stop", "dry_multiplier", 
        "dry_base", "dry_allowed_length", "dry_penalty_last_n", 
        "dry_sequence_breakers", "skew", "xtc_probability", "xtc_threshold", 
        "samplers", "speculative_n", "speculative_k", "speculative_alpha", 
        "speculative_temperature"
    }
    
    filtered = {k: v for k, v in mapped.items() if k in whitelist}
    
    # 特殊字段处理
    if "grammar" in filtered:
        grammar_val = filtered["grammar"]
        if not grammar_val or grammar_val == "":
            del filtered["grammar"]

    # logit_bias特殊处理
    if "logit_bias" in filtered:
        lb = filtered["logit_bias"]
        if not lb:                          
            del filtered["logit_bias"]
        elif isinstance(lb, list):
            if len(lb) == 0:
                del filtered["logit_bias"]
            else:
                try:
                    filtered["logit_bias"] = {int(item[0]): item[1] for item in lb}
                except Exception:
                    del filtered["logit_bias"]  

    # stop序列特殊处理
    if "stop" in filtered:
        stop_val = filtered["stop"]
        if isinstance(stop_val, list):
            cleaned = list(dict.fromkeys(s for s in stop_val if s))
            if cleaned:
                filtered["stop"] = cleaned
            else:
                del filtered["stop"]
        elif not stop_val:                  
            del filtered["stop"]

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
        # 现在不需要在初始化时验证模型文件，因为将由外部llama.cpp服务器处理
        self.model_path = getattr(self.config.model, 'path', '')
        self.model: Optional[LlamaCppClient] = None
        self.openai_client: Optional[LlamaModelClient] = None  # OpenAI兼容客户端
        # 初始化不需要模型文件，只建立到远程服务的连接客户端
        self.openai_client = LlamaModelClient(
            model_path=self.model_path or './dummy.gguf',  # 使用虚拟路径
            host=getattr(self.config.service, 'host', '127.0.0.1'),
            port=getattr(self.config.service, 'port', 31301)
        )

    def connect_to_llama_server(self):
        """连接到预启动的llama.cpp服务器（不再在此处管理服务器进程）"""
        # 现在我们只连接到一个预运行的llama.cpp服务器，而不是在此处启动
        host = getattr(self.config.service, 'host', '127.0.0.1')
        port = getattr(self.config.service, 'port', 31301)
        
        # 创建HTTP API客户端连接
        self.model = LlamaCppClient(server_url=f"http://{host}:{port}")
        print(f"Connected to llama server at http://{host}:{port}")

    @classmethod
    def get_instance(cls, config: Config = None) -> "ModelManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config or Config.from_env())
        return cls._instance

    def get_model(self) -> Optional[LlamaCppClient]:
        if self.model is None:
            self.connect_to_llama_server()
        return self.model

    def get_openai_client(self) -> Optional[LlamaModelClient]:
        """获取OpenAI接口兼容的客户端"""
        return self.openai_client

    def get_model_name(self) -> str:
        """Get the name of the loaded model.

        Returns:
            Model filename or empty string if no model loaded.
        """
        if not self.model_path:
            return "remote_llama_cpp"
        return Path(self.model_path).name

    def reload_model(self, model_path: str = None):
        # 更新配置，但不重启服务器
        if model_path:
            self.model_path = model_path
            self.config.model.path = model_path
            
        # 重新连接新配置
        self.connect_to_llama_server()

    # ------------------------------------------------------------------
    # 流式生成
    # ------------------------------------------------------------------
    async def stream_generate(
        self,
        prompt: str,
        params: dict = None,
    ) -> AsyncGenerator[dict, None]:  # Changed to dict to match expected return type
        """
        异步流式生成（真正的流式生成，逐token返回）。
        """
        from llama.core.logger_manager import logger

        model = self.get_model() if self.model else None
        if model is None:
            raise RuntimeError("Model is not loaded")

        raw_params = dict(params or {})
        raw_params["stream"] = True
        clean_params = filter_llama_params(raw_params)

        # 强制最大 token 上限保护（生产必须限制）
        MAX_ALLOWED_TOKENS = 4096
        if "n_predict" in clean_params:
            clean_params["n_predict"] = min(
                int(clean_params["n_predict"]),
                MAX_ALLOWED_TOKENS,
            )
        else:
            clean_params["n_predict"] = 512

        logger.info(f"stream_generate clean_params keys: {list(clean_params.keys())}")

        try:
            chunk_index = 0
            accumulated_content = ""
            
            for chunk_data in model.stream_completion(prompt, **clean_params):
                # 确保chunk_data是一个字典类型
                if not isinstance(chunk_data, dict):
                    continue
                    
                text_from_model = chunk_data.get("content", "")
                
                if text_from_model:
                    # 获取模型文件名用于填充响应
                    model_filename = self.get_model_name()
                    
                    # 构造符合原来llama-cpp-python输出的格式
                    formatted_chunk_data = {
                        "choices": [{
                            "text": text_from_model,
                            "index": chunk_index,
                            "logprobs": None,
                            "finish_reason": None
                        }],
                        "created": int(time.time()),
                        "model": model_filename,
                        "object": "text_completion",
                        "id": f"cmpl-{uuid.uuid4().hex[:8]}"
                    }
                    
                    yield formatted_chunk_data
                    chunk_index += 1
                    logger.info(f"Generated token: {repr(text_from_model)} (model: {model_filename})")
                    
                # 检查结束标志
                if chunk_data.get("stop", False):
                    break

        except Exception as e:
            logger.error(f"Error in stream generation: {e}", exc_info=True)
            raise

    # ------------------------------------------------------------------
    # 非流式生成（同步包装为异步）
    # ------------------------------------------------------------------
    async def generate(self, prompt: str, params: dict = None) -> dict:
        """
        非流式生成，返回完整的 llama.cpp 原始响应 dict。
        """
        from llama.core.logger_manager import logger
        
        model = self.get_model() if self.model else None
        if model is None:
            raise RuntimeError("Model is not loaded")

        raw_params = dict(params or {})
        raw_params["stream"] = False
        clean_params = filter_llama_params(raw_params)

        loop = asyncio.get_event_loop()
        try:
            # 在线程池中执行HTTP请求
            result = await loop.run_in_executor(
                None, 
                lambda: model.completion(prompt, **clean_params)
            )
            
            # 将llama.cpp结果格式化为兼容原有api的格式
            model_filename = self.get_model_name()
            content = result.get("content", "") if isinstance(result, dict) else str(result)
            
            # 提取和计算token数量
            tokens_evaluated = result.get("tokens_evaluated", 0)
            tokens_predicted = result.get("tokens_predicted", len(content.split()))
            
            # 构建与原llama-cpp-python兼容的_RESPONSE
            compatible_response = {
                "choices": [{
                    "text": content,
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "stop"
                }],
                "created": int(time.time()),
                "model": model_filename,
                "object": "text_completion",
                "id": f"cmpl-{uuid.uuid4().hex[:8]}",
                "usage": {
                    "prompt_tokens": tokens_evaluated,
                    "completion_tokens": tokens_predicted,
                    "total_tokens": tokens_evaluated + tokens_predicted
                }
            }
            
            return compatible_response
            
        except Exception as e:
            logger.error(f"Error in model non-stream generation: {e}", exc_info=True)
            raise
    
    def shutdown(self) -> bool:
        """关闭服务器进程 - 现在什么都不做，因为我们不管理外部服务器"""
        # 只断开连接
        self.model = None
        return True