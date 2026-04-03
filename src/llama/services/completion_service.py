import time
import uuid
from typing import AsyncGenerator, Optional, Dict, Any

from llama.core.model_manager import ModelManager, filter_llama_params
from llama.config.config import Config
from llama.models.legacy.completion_request import CompletionRequest
from llama.models.legacy.completion_response import CompletionResponse
from llama.models.common.stream_chunk import StreamChunk
from llama.exceptions.service_error import ServiceError
from llama.core.logger_manager import logger
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


def _build_llama_params(request: CompletionRequest) -> Dict[str, Any]:
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

    async def generate_stream(
        self, request: CompletionRequest
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式文本生成，逐 chunk yield 官方llama.cpp格式的字典

        Args:
            request: Completion request data.

        Yields:
            Token chunk dictionaries in OpenAI format.
        """
        model_name = request.model if request.model else self.model_manager.get_model_name()
        logger.info(f"CompletionService.generate_stream called for model: {model_name}, prompt length: {len(request.prompt) if isinstance(request.prompt, str) else len(request.prompt[0])}")

        model = self.model_manager.get_model()
        if model is None:
            raise ServiceError("Model not loaded")

        prompt = request.prompt if isinstance(request.prompt, str) else request.prompt[0]
        params = _build_llama_params(request)

        if "temperature" in params and params["temperature"] > 1.0:
            params["temperature"] = 1.0

        request_id = f"cmpl-{uuid.uuid4().hex[:8]}"
        created = int(time.time())
        index = 0

        start_time = time.time()
        logger.info(f"Starting stream generation for request {request_id}, params: {list(params.keys())}")

        try:
            async for chunk in self.model_manager.stream_generate(prompt, params):
                choices = chunk.get("choices", [])
                if choices:
                    choices[0]["index"] = index
                chunk["id"] = request_id
                chunk["created"] = created
                chunk["model"] = model_name
                yield chunk
                index += 1

            elapsed_time = time.time() - start_time
            logger.info(f"Stream generation completed for request {request_id}, total chunks: {index}, elapsed time: {elapsed_time:.2f}s")

            yield {
                "choices": [{
                    "text": "",
                    "index": index,
                    "logprobs": None,
                    "finish_reason": "length"
                }],
                "created": created,
                "model": model_name,
                "object": "text_completion",
                "id": request_id
            }

        except Exception as e:
            logger.error(f"CompletionService.generate_stream error: {e}", exc_info=True)
            raise ServiceError(f"Model generation failed: {e}")

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        """
        非流式文本生成，返回完整 CompletionResponse

        Args:
            request: Completion request data.

        Returns:
            CompletionResponse with generated text.
        """
        model_name = request.model if request.model else self.model_manager.get_model_name()
        logger.info(f"CompletionService.generate called for model: {model_name}, prompt length: {len(request.prompt) if isinstance(request.prompt, str) else len(request.prompt[0])}")

        model = self.model_manager.get_model()
        if model is None:
            raise ServiceError("Model not loaded")

        prompt = request.prompt if isinstance(request.prompt, str) else request.prompt[0]
        params = _build_llama_params(request)

        if "temperature" in params and params["temperature"] > 1.0:
            params["temperature"] = 1.0

        start_time = time.time()
        logger.info(f"Starting non-stream generation for params: {list(params.keys())}")

        try:
            result = await self.model_manager.generate(prompt, params)
        except Exception as e:
            logger.error(f"CompletionService.generate error: {e}", exc_info=True)
            raise ServiceError(f"Model generation failed: {e}")

        elapsed_time = time.time() - start_time
        logger.info(f"Non-stream generation completed, elapsed time: {elapsed_time:.2f}s")

        choices = result.get("choices", [])
        usage = result.get("usage", {})

        return CompletionResponse(
            id=result.get("id", f"cmpl-{uuid.uuid4().hex[:8]}"),
            object="text_completion",
            created=result.get("created", int(time.time())),
            model=model_name,
            choices=[
                {
                    "text": c.get("text", ""),
                    "index": c.get("index", 0),
                    "logprobs": c.get("logprobs"),
                    "finish_reason": c.get("finish_reason", "stop"),
                }
                for c in choices
            ],
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )