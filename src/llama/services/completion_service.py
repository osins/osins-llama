from typing import AsyncGenerator
from fastapi import Request
from src.llama.models.legacy.completion_request import CompletionRequest
from src.llama.models.legacy.completion_response import CompletionResponse
from src.llama.models.common.stream_chunk import StreamChunk
from src.llama.core.model_manager import ModelManager
from src.llama.config.config import Config
from src.llama.utils.token_utils import count_tokens
import asyncio
import time
import uuid
from src.llama.exceptions import ServiceError


class CompletionService:
    """
    Completion服务类
    处理文本生成请求，包括流式和非流式响应
    """

    _instance = None

    def __init__(self, config: Config = None):
        # If no config is provided, try to get it from the app state
        # This avoids re-loading config from environment when running inside the API server
        self.config = config
        if self.config is None:
            # Fallback to environment if not running in API server context
            self.config = Config.from_env()
        self.model_manager = ModelManager.get_instance(self.config)

    @classmethod
    def get_instance(cls, config: Config = None):
        """
        获取CompletionService单例实例
        """
        if cls._instance is None:
            cls._instance = cls(config)
        elif config is not None:
            # If a config is provided and instance already exists, update the config
            cls._instance.config = config
        return cls._instance

    def _validate_request(self, request: CompletionRequest):
        """
        验证请求参数

        Args:
            request: Completion请求对象

        Raises:
            ValueError: 参数验证失败时抛出
        """
        from src.llama.core.logger_manager import logger
        logger.info("_validate_request called")

        # 验证模型名称
        if not request.model or len(request.model.strip()) == 0:
            logger.error("Model name is required")
            raise ValueError("Model name is required")

        logger.info(f"Model validation passed: {request.model}")

        # 验证prompt
        if request.prompt is None:
            logger.error("Prompt is required")
            raise ValueError("Prompt is required")

        logger.info(f"Prompt is not None, type: {type(request.prompt)}")

        if isinstance(request.prompt, str):
            if len(request.prompt.strip()) == 0:
                logger.error("Prompt cannot be empty")
                raise ValueError("Prompt cannot be empty")
        elif isinstance(request.prompt, list):
            if len(request.prompt) == 0:
                logger.error("Prompt list cannot be empty")
                raise ValueError("Prompt list cannot be empty")
            for i, p in enumerate(request.prompt):
                if not isinstance(p, str) or len(p.strip()) == 0:
                    logger.error(f"Prompt at index {i} cannot be empty")
                    raise ValueError(f"Prompt at index {i} cannot be empty")

        logger.info("Prompt validation passed")

        # 验证max_tokens
        if request.max_tokens is not None and request.max_tokens <= 0:
            logger.error(f"max_tokens must be positive, got: {request.max_tokens}")
            raise ValueError("max_tokens must be positive")

        logger.info(f"max_tokens validation passed: {request.max_tokens}")

        # 验证temperature
        if request.temperature is not None:
            temp = request.temperature
            if temp < 0.0 or temp > 2.0:
                logger.error(f"temperature must be between 0.0 and 2.0, got: {temp}")
                raise ValueError("temperature must be between 0.0 and 2.0")

        logger.info(f"temperature validation passed: {request.temperature}")

        # 验证top_p
        if request.top_p is not None:
            topp = request.top_p
            if topp <= 0.0 or topp > 1.0:
                logger.error(f"top_p must be between 0.0 and 1.0, got: {topp}")
                raise ValueError("top_p must be between 0.0 and 1.0")

        logger.info(f"top_p validation passed: {request.top_p}")

        # 验证n
        if request.n is not None:
            n_val = request.n
            if n_val <= 0 or n_val > 128:
                logger.error(f"n must be between 1 and 128, got: {n_val}")
                raise ValueError("n must be between 1 and 128")

        logger.info(f"n validation passed: {request.n}")

        # 验证presence_penalty
        if request.presence_penalty is not None:
            penalty = request.presence_penalty
            if penalty < -2.0 or penalty > 2.0:
                logger.error(f"presence_penalty must be between -2.0 and 2.0, got: {penalty}")
                raise ValueError("presence_penalty must be between -2.0 and 2.0")

        logger.info(f"presence_penalty validation passed: {request.presence_penalty}")

        # 验证frequency_penalty
        if request.frequency_penalty is not None:
            freq_penalty = request.frequency_penalty
            if freq_penalty < -2.0 or freq_penalty > 2.0:
                logger.error(f"frequency_penalty must be between -2.0 and 2.0, got: {freq_penalty}")
                raise ValueError("frequency_penalty must be between -2.0 and 2.0")

        logger.info("All validations passed")

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        """
        生成非流式响应

        Args:
            request: Completion请求对象

        Returns:
            CompletionResponse: 完整的响应对象
        """
        from src.llama.core.logger_manager import logger
        logger.info("CompletionService.generate called")

        try:
            # 验证请求参数
            self._validate_request(request)
            logger.info("Request validation passed")

            # 获取模型实例
            model = self.model_manager.get_model()
            if model is None:
                raise ServiceError("Model not loaded")

            # 检查token数量
            prompt_tokens = 0
            if isinstance(request.prompt, str):
                prompt_tokens = count_tokens(request.prompt)
            else:
                # 如果是多个prompt，计算总token数
                for prompt in request.prompt:
                    prompt_tokens += count_tokens(prompt)

            if prompt_tokens > self.config.resources.max_prompt_tokens:
                raise ValueError(f"Prompt exceeds maximum token count: {self.config.resources.max_prompt_tokens}")

            # 生成响应
            start_time = time.time()

            # 根据请求参数生成文本
            if isinstance(request.prompt, str):
                prompt = request.prompt
            else:
                # 如果是多个prompt，只使用第一个
                prompt = request.prompt[0] if request.prompt else ""

            try:
                # 构建模型调用参数字典，只包含支持的参数
                model_kwargs = {
                    "prompt": prompt,
                    "max_tokens": request.max_tokens or request.max_new_tokens or 16,
                    "temperature": request.temperature or 1.0,
                    "top_p": request.top_p or 1.0,
                    "top_k": request.top_k or 40,
                    "stream": False,  # 非流式
                    "logprobs": getattr(request, 'logprobs', None),
                    "echo": getattr(request, 'echo', False),
                    "stop": request.stop,
                    "presence_penalty": request.presence_penalty or 0.0,
                    "frequency_penalty": request.frequency_penalty or 0.0,
                    "logit_bias": request.logit_bias
                }

                # 添加其他可选参数，如果它们存在的话
                if request.n is not None:
                    model_kwargs["n"] = request.n
                if request.best_of is not None:
                    model_kwargs["best_of"] = request.best_of
                if request.repetition_penalty is not None:
                    model_kwargs["repetition_penalty"] = request.repetition_penalty
                if request.min_p is not None:
                    model_kwargs["min_p"] = request.min_p
                if request.typical_p is not None:
                    model_kwargs["typical_p"] = request.typical_p
                if request.tfs is not None:
                    model_kwargs["tfs"] = request.tfs
                if request.mirostat_mode is not None:
                    model_kwargs["mirostat_mode"] = request.mirostat_mode
                if request.mirostat_tau is not None:
                    model_kwargs["mirostat_tau"] = request.mirostat_tau
                if request.mirostat_eta is not None:
                    model_kwargs["mirostat_eta"] = request.mirostat_eta

                response = model(**model_kwargs)

                # 验证响应格式
                if not isinstance(response, dict) or "choices" not in response:
                    raise ServiceError("Invalid model response format")
            except Exception as e:
                raise ServiceError(f"Model generation failed: {str(e)}")

            # 解析模型响应
            choices = []
            if "choices" in response and isinstance(response["choices"], list):
                for idx, choice in enumerate(response["choices"]):
                    # 验证choice格式
                    if not isinstance(choice, dict):
                        raise ServiceError(f"Invalid choice format at index {idx}")

                    # 构造选择项
                    from src.llama.models.legacy.completion_choice import CompletionChoice
                    from src.llama.models.legacy.completion_finish_reason import CompletionFinishReason

                    finish_reason_str = choice.get("finish_reason", "stop")
                    # 将字符串转换为枚举值
                    try:
                        finish_reason = CompletionFinishReason(finish_reason_str)
                    except ValueError:
                        # 如果不是有效的枚举值，默认为stop
                        finish_reason = CompletionFinishReason.STOP
                        
                    text = choice.get("text", "")

                    logprobs = choice.get("logprobs", None)
                    completion_choice = CompletionChoice(
                        text=text,
                        index=idx,
                        logprobs=logprobs,
                        finish_reason=finish_reason
                    )
                    choices.append(completion_choice)
            else:
                # 如果没有choices，创建一个默认选择
                from src.llama.models.legacy.completion_choice import CompletionChoice
                from src.llama.models.legacy.completion_finish_reason import CompletionFinishReason
                completion_choice = CompletionChoice(
                    text="",
                    index=0,
                    logprobs=None,
                    finish_reason=CompletionFinishReason.STOP
                )
                choices = [completion_choice]

            # 计算用量
            from src.llama.models.common.usage import Usage
            prompts = request.prompt if isinstance(request.prompt, list) else [request.prompt]
            prompt_tokens = sum(count_tokens(prompt) for prompt in prompts)
            completion_tokens = sum(count_tokens(choice.text) for choice in choices)
            total_tokens = prompt_tokens + completion_tokens

            usage = Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )

            # 构造响应对象，确保所有必需字段都有值
            response_obj = CompletionResponse(
                id=f"cmpl-{uuid.uuid4().hex}",
                created=int(start_time),
                model=request.model,
                choices=choices,
                usage=usage
            )

            return response_obj
        except ValueError as ve:
            # 捕获参数验证错误
            raise ve
        except ServiceError:
            # 重新抛出服务错误
            raise
        except Exception as e:
            # 捕获其他异常并重新抛出
            raise ServiceError(f"Unexpected error during generation: {str(e)}")

    async def generate_stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        """
        生成流式响应

        Args:
            request: Completion请求对象

        Yields:
            StreamChunk: 流式数据块
        """
        try:
            # 验证请求参数
            self._validate_request(request)

            # 获取模型实例
            model = self.model_manager.get_model()
            if model is None:
                raise ServiceError("Model not loaded")

            # 检查token数量
            prompt_tokens = 0
            if isinstance(request.prompt, str):
                prompt_tokens = count_tokens(request.prompt)
            else:
                # 如果是多个prompt，计算总token数
                for prompt in request.prompt:
                    prompt_tokens += count_tokens(prompt)

            if prompt_tokens > self.config.resources.max_prompt_tokens:
                raise ValueError(f"Prompt exceeds maximum token count: {self.config.resources.max_prompt_tokens}")

            # 生成流式响应
            if isinstance(request.prompt, str):
                prompt = request.prompt
            else:
                # 如果是多个prompt，只使用第一个
                prompt = request.prompt[0] if request.prompt else ""

            try:
                # 由于llama-cpp-python的流式功能，我们模拟流式响应
                # 实际应用中，这里应该是真正的流式生成
                # 构建模型调用参数字典，只包含支持的参数
                model_kwargs = {
                    "prompt": prompt,
                    "max_tokens": request.max_tokens or request.max_new_tokens or 16,
                    "temperature": request.temperature or 1.0,
                    "top_p": request.top_p or 1.0,
                    "top_k": request.top_k or 40,
                    "stream": True,  # 流式
                    "logprobs": getattr(request, 'logprobs', None),
                    "echo": getattr(request, 'echo', False),
                    "stop": request.stop,
                    "presence_penalty": request.presence_penalty or 0.0,
                    "frequency_penalty": request.frequency_penalty or 0.0,
                    "logit_bias": request.logit_bias
                }
                
                # 添加其他可选参数，如果它们存在的话
                if request.n is not None:
                    model_kwargs["n"] = request.n
                if request.best_of is not None:
                    model_kwargs["best_of"] = request.best_of
                if request.repetition_penalty is not None:
                    model_kwargs["repetition_penalty"] = request.repetition_penalty
                if request.min_p is not None:
                    model_kwargs["min_p"] = request.min_p
                if request.typical_p is not None:
                    model_kwargs["typical_p"] = request.typical_p
                if request.tfs is not None:
                    model_kwargs["tfs"] = request.tfs
                if request.mirostat_mode is not None:
                    model_kwargs["mirostat_mode"] = request.mirostat_mode
                if request.mirostat_tau is not None:
                    model_kwargs["mirostat_tau"] = request.mirostat_tau
                if request.mirostat_eta is not None:
                    model_kwargs["mirostat_eta"] = request.mirostat_eta
                
                response_generator = model(**model_kwargs)
            except Exception as e:
                raise ServiceError(f"Model generation failed: {str(e)}")

            # 生成ID
            gen_id = f"cmpl-{uuid.uuid4().hex}"
            created_time = int(time.time())

            # 模拟流式输出
            full_text = ""
            for chunk in response_generator:
                # 检查是否取消请求
                if asyncio.current_task().cancelled():
                    break
                
                # 验证chunk格式
                if not isinstance(chunk, dict) or "choices" not in chunk:
                    raise ServiceError("Invalid chunk format from model")
                
                # 提取文本片段
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    choice = chunk["choices"][0]
                    if not isinstance(choice, dict):
                        raise ServiceError("Invalid choice format in chunk")
                        
                    delta_text = choice.get("text", "")
                    full_text += delta_text

                    # 创建流式数据块
                    stream_chunk = StreamChunk(
                        id=gen_id,
                        object="text_completion.chunk",
                        created=created_time,
                        model=request.model,
                        choices=[
                            {
                                "text": delta_text,
                                "index": 0,
                                "logprobs": choice.get("logprobs", None),
                                "finish_reason": None
                            }
                        ]
                    )

                    yield stream_chunk

            # 发送结束块
            end_chunk = StreamChunk(
                id=gen_id,
                object="text_completion.chunk",
                created=created_time,
                model=request.model,
                choices=[
                    {
                        "text": "",
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": "stop"
                    }
                ]
            )

            yield end_chunk
        except ValueError as ve:
            # 捕获参数验证错误
            raise ve
        except ServiceError:
            # 重新抛出服务错误
            raise
        except Exception as e:
            # 捕获其他异常并重新抛出
            raise ServiceError(f"Unexpected error during streaming: {str(e)}")