from llama_cpp import Llama
from pathlib import Path
import threading
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

        self.model = Llama(
            model_path=self.model_path,
            n_ctx=self.config.model.n_ctx,
            n_threads=self.config.model.n_threads,
            verbose=self.config.model.verbose,
        )

        print(f"Model loaded successfully: {Path(self.model_path).name}")

    @classmethod
    def get_instance(cls, config: Config = None) -> "ModelManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    def get_model(self) -> Optional[Llama]:
        return self.model

    def reload_model(self, model_path: str = None):
        if model_path:
            self.model_path = model_path
            self.config.model.path = model_path
        self._load_model()

    # ------------------------------------------------------------------
    # 流式生成
    #
    # 实现说明：
    #   llama-cpp-python 的流式生成器是同步的，在 run_in_executor 线程池
    #   中无法可靠地逐 token yield 给 asyncio。最稳定的方案是：
    #     1. 用 stream=True 在线程池中完整生成
    #     2. 将取完整文本后，在 async 层按块 yield 模拟流式效果
    # ------------------------------------------------------------------
    async def stream_generate(
        self,
        prompt: str,
        params: dict = None,
    ) -> AsyncGenerator[str, None]:
        """
        异步流式生成（先完整生成，再逐步 yield 模拟流式）。

        Args:
            prompt:  输入提示词
            params:  生成参数（原始请求参数，会自动过滤不支持的字段）

        Yields:
            文本片段（每次约 4 个字符）
        """
        from src.llama.core.logger_manager import logger

        if self.model is None:
            raise RuntimeError("Model is not loaded")

        raw_params = dict(params or {})
        # 使用流式调用，获取完整响应
        raw_params["stream"] = True
        clean_params = filter_llama_params(raw_params)

        logger.info(f"stream_generate clean_params keys: {list(clean_params.keys())}")

        loop = asyncio.get_event_loop()

        def _sync_generate():
            # 使用流式模式获取完整的生成器
            try:
                return list(self.model(prompt, **clean_params))
            except Exception as e:
                logger.error(f"Error in model stream generation: {e}", exc_info=True)
                raise

        # 在线程池执行同步生成，避免阻塞 asyncio event loop
        chunks = await loop.run_in_executor(None, _sync_generate)

        # 将所有文本片段拼接起来
        full_text = ""
        for chunk in chunks:
            try:
                text = chunk["choices"][0].get("text", "")
                full_text += text
            except (KeyError, IndexError, TypeError):
                continue

        logger.info(f"stream_generate: generated {len(full_text)} chars | text={repr(full_text)}")

        if not full_text:
            logger.warning("stream_generate: empty output from model")
            return

        # 按块 yield，模拟流式输出（每块约 4 字符，对中文约 2 个字）
        chunk_size = 4
        for i in range(0, len(full_text), chunk_size):
            yield full_text[i: i + chunk_size]
            await asyncio.sleep(0)  # 让出控制权，保证异步调度

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