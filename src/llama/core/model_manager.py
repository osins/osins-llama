from llama_cpp import Llama
from pathlib import Path
import threading
import time
import uuid
from src.llama.config.config import Config
import asyncio
from typing import AsyncGenerator, Optional

# ============================================================
# llama-cpp-python Llama.__call__() 支持的参数白名单
# SillyTavern / OpenAI 发来的其他参数一律过滤，避免
# "unexpected keyword argument" 错误反复出现
# ============================================================
LLAMA_VALID_PARAMS = {
    "suffix",
    "max_tokens",
    "temperature",
    "top_p",
    "min_p",
    "typical_p",
    "logprobs",
    "echo",
    "stop",
    "frequency_penalty",
    "presence_penalty",
    "repeat_penalty",
    "top_k",
    "stream",
    "seed",
    "tfs_z",
    "mirostat_mode",
    "mirostat_tau",
    "mirostat_eta",
    "stopping_criteria",
    "logits_processor",
    "grammar",
    "logit_bias",
}


# SillyTavern / OpenAI 请求字段 → llama-cpp-python 参数名 映射表
# 如果字段名相同则不需要出现在此表中，只映射"别名"字段
_PARAM_ALIAS_MAP = {
    # 同义的 max_tokens 字段，统一映射到 max_tokens
    "max_new_tokens":          "max_tokens",
    "n_predict":               "max_tokens",
    "num_predict":             "max_tokens",
    # 同义的 repeat_penalty 字段
    "repetition_penalty":      "repeat_penalty",
    "rep_pen":                 "repeat_penalty",
    # 同义的 stop 字段
    "stopping_strings":        "stop",
    # 同义的 mirostat_mode 字段
    "mirostat":                "mirostat_mode",
    # 同义的 tfs_z 字段
    "tfs":                     "tfs_z",
}


def filter_llama_params(params: dict) -> dict:
    """
    过滤掉 llama-cpp-python 不支持的参数，只保留白名单中的参数。

    SillyTavern 会发送大量 OpenAI 兼容参数（n, best_of, cache_prompt,
    samplers, dry_multiplier 等），llama-cpp-python 不认识这些字段，
    直接透传会导致 TypeError。此函数统一过滤，一劳永逸。

    特殊处理：
      - grammar:   必须是 LlamaGrammar 对象或 None，空字符串 "" 会导致
                   AttributeError: 'str' object has no attribute 'reset'
                   因此空字符串视为未设置，直接丢弃。
      - logit_bias: 空列表 [] 无意义，丢弃（llama-cpp-python 期望 dict）。
      - stop:      去重、去空值后若为空列表则丢弃。
    """
    # Step 1: 按别名映射表重命名字段并处理同义参数
    mapped: dict = {}
    for key, value in params.items():
        target = _PARAM_ALIAS_MAP.get(key, key)

        if target == "max_tokens" and "max_tokens" in mapped:
            # 多个同义字段时取最大值
            mapped["max_tokens"] = max(mapped["max_tokens"], value)
        elif target == "repeat_penalty" and "repeat_penalty" in mapped:
            # 多个同义字段时取最大值
            mapped["repeat_penalty"] = max(mapped["repeat_penalty"], value)
        elif target == "stop" and "stop" in mapped:
            # 合并去重
            existing = mapped["stop"] if isinstance(mapped["stop"], list) else [mapped["stop"]]
            new_val  = value          if isinstance(value, list)          else [value]
            merged   = list(dict.fromkeys(existing + new_val))
            mapped["stop"] = merged
        else:
            mapped[target] = value

    # Step 2: 通过白名单过滤
    filtered = {k: v for k, v in mapped.items() if k in LLAMA_VALID_PARAMS}

    # --- grammar：只允许 LlamaGrammar 对象或 None，其他类型（如字符串）一律移除 ---
    if "grammar" in filtered:
        from llama_cpp import LlamaGrammar
        grammar_val = filtered["grammar"]
        if grammar_val is not None and not isinstance(grammar_val, LlamaGrammar):
            del filtered["grammar"]

    # --- logit_bias：空列表无意义，移除；list 转 dict（兼容 SillyTavern 格式）---
    if "logit_bias" in filtered:
        lb = filtered["logit_bias"]
        if not lb:                          # None / [] / {} 均视为未设置
            del filtered["logit_bias"]
        elif isinstance(lb, list):
            # SillyTavern 可能发 [] 或 [[token_id, bias], ...]
            if len(lb) == 0:
                del filtered["logit_bias"]
            else:
                try:
                    filtered["logit_bias"] = {int(item[0]): item[1] for item in lb}
                except Exception:
                    del filtered["logit_bias"]  # 格式异常，安全丢弃

    # --- stop：去重去空，空列表则移除 ---
    if "stop" in filtered:
        stop_val = filtered["stop"]
        if isinstance(stop_val, list):
            cleaned = list(dict.fromkeys(s for s in stop_val if s))
            if cleaned:
                filtered["stop"] = cleaned
            else:
                del filtered["stop"]
        elif not stop_val:                  # None 或空字符串
            del filtered["stop"]

    return filtered


class ModelManager:
    """
    模型管理器
    负责模型的加载、管理和生命周期控制
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, config: Config = None):
        self.config = config or Config.from_env()
        self.model_path = self.config.model.path
        self.model: Optional[Llama] = None
        self._load_model()

    def _load_model(self):
        if not self.model_path:
            raise ValueError("Model path is not set")

        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        print(f"Loading model: {Path(self.model_path).name}")

        n_gpu_layers = self.config.model.n_gpu_layers
        if n_gpu_layers == -1:
            n_gpu_layers = 100

        self.model = Llama(
            model_path=self.model_path,
            n_ctx=self.config.model.n_ctx,
            n_threads=self.config.model.n_threads,
            n_gpu_layers=n_gpu_layers,
            n_batch=self.config.model.n_batch,
            verbose=self.config.model.verbose,
        )

        print(f"Model loaded successfully: {Path(self.model_path).name}")
        print(f"GPU layers: {n_gpu_layers}, Batch size: {self.config.model.n_batch}")

    @classmethod
    def get_instance(cls, config: Config = None) -> "ModelManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    def get_model(self) -> Optional[Llama]:
        return self.model

    def get_model_name(self) -> str:
        """Get the name of the loaded model.

        Returns:
            Model filename or empty string if no model loaded.
        """
        if not self.model_path:
            return ""
        return Path(self.model_path).name

    def reload_model(self, model_path: str = None):
        if model_path:
            self.model_path = model_path
            self.config.model.path = model_path
        self._load_model()

    # ------------------------------------------------------------------
    # 流式生成
    #
    # 实现说明：
    #   使用线程生产 + async 队列桥接的方式实现真正的流式生成
    #   1. 在单独线程中运行模型生成
    #   2. 通过 asyncio.Queue 在线程和协程之间传递数据
    #   3. 使用 call_soon_threadsafe 保证线程安全
    # ------------------------------------------------------------------
    async def stream_generate(
        self,
        prompt: str,
        params: dict = None,
    ) -> AsyncGenerator[str, None]:
        """
        异步流式生成（真正的流式生成，逐token返回）。

        Args:
            prompt:  输入提示词
            params:  生成参数（原始请求参数，会自动过滤不支持的字段）

        Yields:
            生成的文本片段
        """
        from src.llama.core.logger_manager import logger

        if self.model is None:
            raise RuntimeError("Model is not loaded")

        raw_params = dict(params or {})
        raw_params["stream"] = True
        clean_params = filter_llama_params(raw_params)

        # 强制最大 token 上限保护（生产必须限制）
        MAX_ALLOWED_TOKENS = 4096
        if "max_tokens" in clean_params:
            clean_params["max_tokens"] = min(
                int(clean_params["max_tokens"]),
                MAX_ALLOWED_TOKENS,
            )
        else:
            clean_params["max_tokens"] = 512

        logger.info(f"stream_generate clean_params keys: {list(clean_params.keys())}")

        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        loop = asyncio.get_running_loop()

        cancel_event = threading.Event()
        generation_error: Optional[Exception] = None

        def callback(chunk):
            # 将完整的chunk放入异步队列
            if not cancel_event.is_set():
                loop.call_soon_threadsafe(queue.put_nowait, chunk)

        def producer():
            nonlocal generation_error
            try:
                # 使用回调方式逐 token 处理
                for chunk in self.model(prompt, **clean_params):
                    if cancel_event.is_set():
                        break
                    
                    # 使用回调函数发送完整chunk
                    callback(chunk)

            except Exception as e:
                generation_error = e
            finally:
                # 发送结束信号
                loop.call_soon_threadsafe(queue.put_nowait, None)

        # 在线程中运行模型
        thread = threading.Thread(target=producer, daemon=True)
        thread.start()

        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    if not thread.is_alive() or cancel_event.is_set():
                        break
                    continue

                if item is None:
                    break

                if isinstance(item, Exception):
                    raise item

                # 从完整chunk中提取文本
                try:
                    text = item["choices"][0].get("text", "")
                except Exception:
                    continue

                if text:
                    # 提取模型文件名
                    model_filename = self.model_path.replace('\\', '/').split('/')[-1]
                    # 返回完整chunk而不是纯文本
                    chunk_data = {
                        "choices": [{
                            "text": text,
                            "index": 0,  # 实际索引将在CompletionService中处理
                            "logprobs": None,
                            "finish_reason": None
                        }],
                        "created": int(time.time()),
                        "model": model_filename,
                        "object": "text_completion",
                        "id": f"cmpl-{uuid.uuid4().hex[:8]}"
                    }
                    yield chunk_data
                    logger.info(f"Generated token: {repr(text)} (model: {model_filename})")

            if generation_error:
                raise generation_error

        finally:
            cancel_event.set()
            thread.join(timeout=2)

    # ------------------------------------------------------------------
    # 非流式生成（同步包装为异步）
    # ------------------------------------------------------------------
    async def generate(self, prompt: str, params: dict = None) -> dict:
        """
        非流式生成，返回完整的 llama-cpp-python 原始响应 dict。

        Args:
            prompt: 输入提示词
            params: 生成参数（原始请求参数，会自动过滤不支持的字段）

        Returns:
            llama-cpp-python 返回的完整 dict
        """
        from src.llama.core.logger_manager import logger
        
        if self.model is None:
            raise RuntimeError("Model is not loaded")

        raw_params = dict(params or {})
        raw_params["stream"] = False
        clean_params = filter_llama_params(raw_params)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: self.model(prompt, **clean_params)
            )
            return result
        except Exception as e:
            logger.error(f"Error in model non-stream generation: {e}", exc_info=True)
            raise