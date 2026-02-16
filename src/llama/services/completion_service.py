import time
import uuid
from typing import AsyncGenerator, Optional

from src.llama.core.model_manager import ModelManager, filter_llama_params
from src.llama.config.config import Config
from src.llama.models.legacy.completion_request import CompletionRequest
from src.llama.models.legacy.completion_response import CompletionResponse
from src.llama.models.common.stream_chunk import StreamChunk
from src.llama.exceptions.service_error import ServiceError
from src.llama.core.logger_manager import logger

import threading


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


def _build_llama_params(request: CompletionRequest) -> dict:
    """
    将 CompletionRequest 转换为 llama-cpp-python 支持的参数字典。

    处理流程：
      1. 将 request 转为 dict（排除 None 值）
      2. 按别名映射表重命名字段
      3. 合并同义的 stop / stopping_strings
      4. 通过白名单过滤，丢弃所有不支持的字段
    """
    # Step 1: 转为 dict，排除 None
    raw: dict = {
        k: v for k, v in request.model_dump().items()
        if v is not None
    }

    # Step 2: 别名映射（注意：max_tokens 可能被多个字段设置，取最大值）
    mapped: dict = {}
    for key, value in raw.items():
        target = _PARAM_ALIAS_MAP.get(key, key)

        if target == "max_tokens" and "max_tokens" in mapped:
            # 多个同义字段时取最大值
            mapped["max_tokens"] = max(mapped["max_tokens"], value)
        elif target == "repeat_penalty" and "repeat_penalty" in mapped:
            # 以第一个出现的为准
            pass
        elif target == "stop" and "stop" in mapped:
            # 合并去重
            existing = mapped["stop"] if isinstance(mapped["stop"], list) else [mapped["stop"]]
            new_val  = value          if isinstance(value, list)          else [value]
            merged   = list(dict.fromkeys(existing + new_val))
            mapped["stop"] = merged
        else:
            mapped[target] = value

    # 降低 temperature 以提高生成稳定性（如果未指定或值过高）
    if "temperature" not in mapped or mapped["temperature"] > 1.0:
        mapped["temperature"] = 1.0

    # Step 3: 通过白名单过滤（核心修复：丢弃 n, best_of, cache_prompt 等不支持字段）
    clean = filter_llama_params(mapped)

    logger.info(
        f"_build_llama_params: raw keys={list(raw.keys())}, "
        f"clean keys={list(clean.keys())}"
    )
    return clean


class CompletionService:
    """
    文本补全服务
    封装对 ModelManager 的调用，负责将 API 请求转换为模型调用参数
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, config: Config = None):
        self.config = config or Config.from_env()
        self.model_manager = ModelManager.get_instance(config)

    @classmethod
    def get_instance(cls, config: Config = None) -> "CompletionService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    # ------------------------------------------------------------------
    # 流式生成
    # ------------------------------------------------------------------
    async def generate_stream(
        self, request: CompletionRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        流式文本生成，逐 chunk yield StreamChunk
        """
        from src.llama.core.logger_manager import logger
        logger.info(f"CompletionService.generate_stream called for model: {request.model}, prompt length: {len(request.prompt) if isinstance(request.prompt, str) else len(request.prompt[0])}")
        
        model = self.model_manager.get_model()
        if model is None:
            raise ServiceError("Model not loaded")

        prompt = request.prompt if isinstance(request.prompt, str) else request.prompt[0]
        params = _build_llama_params(request)
        
        # 降低 temperature 以提高生成稳定性
        if "temperature" in params and params["temperature"] > 1.0:
            params["temperature"] = 1.0  # 从1.5降低到1.0
        
        request_id = f"cmpl-{uuid.uuid4().hex[:8]}"
        created    = int(time.time())
        index      = 0
        
        # 记录开始生成的时间
        start_time = time.time()
        logger.info(f"Starting stream generation for request {request_id}, params: {list(params.keys())}")

        try:
            async for text in self.model_manager.stream_generate(prompt, params):
                yield StreamChunk(
                    id=request_id,
                    object="text_completion.chunk",
                    created=created,
                    model=request.model,
                    choices=[{
                        "text":          text,
                        "index":         index,
                        "logprobs":      None,
                        "finish_reason": None,
                    }],
                )
                index += 1

            # 最后发送 finish chunk
            elapsed_time = time.time() - start_time
            logger.info(f"Stream generation completed for request {request_id}, total chunks: {index}, elapsed time: {elapsed_time:.2f}s")
            
            yield StreamChunk(
                id=request_id,
                object="text_completion.chunk",
                created=created,
                model=request.model,
                choices=[{
                    "text":          "",
                    "index":         index,
                    "logprobs":      None,
                    "finish_reason": "stop",
                }],
            )

        except Exception as e:
            logger.error(f"CompletionService.generate_stream error: {e}", exc_info=True)
            raise ServiceError(f"Model generation failed: {e}")

    # ------------------------------------------------------------------
    # 非流式生成
    # ------------------------------------------------------------------
    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        """
        非流式文本生成，返回完整 CompletionResponse
        """
        from src.llama.core.logger_manager import logger
        logger.info(f"CompletionService.generate called for model: {request.model}, prompt length: {len(request.prompt) if isinstance(request.prompt, str) else len(request.prompt[0])}")
        
        model = self.model_manager.get_model()
        if model is None:
            raise ServiceError("Model not loaded")

        prompt = request.prompt if isinstance(request.prompt, str) else request.prompt[0]
        params = _build_llama_params(request)
        
        # 降低 temperature 以提高生成稳定性
        if "temperature" in params and params["temperature"] > 1.0:
            params["temperature"] = 1.0  # 从1.5降低到1.0

        # 记录开始生成的时间
        start_time = time.time()
        logger.info(f"Starting non-stream generation for params: {list(params.keys())}")

        try:
            result = await self.model_manager.generate(prompt, params)
        except Exception as e:
            logger.error(f"CompletionService.generate error: {e}", exc_info=True)
            raise ServiceError(f"Model generation failed: {e}")

        # 记录生成完成的时间
        elapsed_time = time.time() - start_time
        logger.info(f"Non-stream generation completed, elapsed time: {elapsed_time:.2f}s")

        # 解析 llama-cpp-python 返回的原始 dict
        choices = result.get("choices", [])
        usage   = result.get("usage", {})

        return CompletionResponse(
            id=result.get("id", f"cmpl-{uuid.uuid4().hex[:8]}"),
            object="text_completion",
            created=result.get("created", int(time.time())),
            model=request.model,
            choices=[
                {
                    "text":          c.get("text", ""),
                    "index":         c.get("index", 0),
                    "logprobs":      c.get("logprobs"),
                    "finish_reason": c.get("finish_reason", "stop"),
                }
                for c in choices
            ],
            usage={
                "prompt_tokens":     usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens":      usage.get("total_tokens", 0),
            },
        )