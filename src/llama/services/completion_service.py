from typing import AsyncGenerator
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
        self.config = config or Config.from_env()
        self.model_manager = ModelManager.get_instance(self.config)

    @classmethod
    def get_instance(cls, config: Config = None):
        """
        获取CompletionService单例实例
        """
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def _validate_request(self, request: CompletionRequest):
        """
        验证请求参数

        Args:
            request: Completion请求对象

        Raises:
            ValueError: 参数验证失败时抛出
        """
        # 验证模型名称
        if not request.model or len(request.model.strip()) == 0:
            raise ValueError("Model name is required")

        # 验证prompt
        if request.prompt is None:
            raise ValueError("Prompt is required")

        if isinstance(request.prompt, str):
            if len(request.prompt.strip()) == 0:
                raise ValueError("Prompt cannot be empty")
        elif isinstance(request.prompt, list):
            if len(request.prompt) == 0:
                raise ValueError("Prompt list cannot be empty")
            for i, p in enumerate(request.prompt):
                if not isinstance(p, str) or len(p.strip()) == 0:
                    raise ValueError(f"Prompt at index {i} cannot be empty")

        # 验证max_tokens
        if request.max_tokens is not None and request.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        # 验证temperature
        if request.temperature is not None:
            temp = request.temperature
            if temp < 0.0 or temp > 2.0:
                raise ValueError("temperature must be between 0.0 and 2.0")

        # 验证top_p
        if request.top_p is not None:
            topp = request.top_p
            if topp <= 0.0 or topp > 1.0:
                raise ValueError("top_p must be between 0.0 and 1.0")

        # 验证n
        if request.n is not None:
            n_val = request.n
            if n_val <= 0 or n_val > 128:
                raise ValueError("n must be between 1 and 128")

        # 验证presence_penalty
        if request.presence_penalty is not None:
            penalty = request.presence_penalty
            if penalty < -2.0 or penalty > 2.0:
                raise ValueError("presence_penalty must be between -2.0 and 2.0")

        # 验证frequency_penalty
        if request.frequency_penalty is not None:
            freq_penalty = request.frequency_penalty
            if freq_penalty < -2.0 or freq_penalty > 2.0:
                raise ValueError("frequency_penalty must be between -2.0 and 2.0")

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        """
        生成非流式响应

        Args:
            request: Completion请求对象

        Returns:
            CompletionResponse: 完整的响应对象
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

            # 生成响应
            start_time = time.time()

            # 根据请求参数生成文本
            if isinstance(request.prompt, str):
                prompt = request.prompt
            else:
                # 如果是多个prompt，只使用第一个
                prompt = request.prompt[0] if request.prompt else ""

            try:
                response = model(
                    prompt=prompt,
                    max_tokens=request.max_tokens or 16,
                    temperature=request.temperature or 1.0,
                    top_p=request.top_p or 1.0,
                    n=request.n or 1,
                    stream=False,  # 非流式
                    logprobs=request.logprobs,
                    echo=request.echo or False,
                    stop=request.stop,
                    presence_penalty=request.presence_penalty or 0.0,
                    frequency_penalty=request.frequency_penalty or 0.0,
                    best_of=request.best_of or 1,
                    logit_bias=request.logit_bias
                )
                
                # 验证响应格式
                if not isinstance(response, dict) or "choices" not in response:
                    raise ServiceError("Invalid model response format")
            except Exception as e:
                raise ServiceError(f"Model generation failed: {str(e)}")

            # 构造响应对象
            response_obj = CompletionResponse(
                id=f"cmpl-{uuid.uuid4().hex}",
                created=int(start_time),
                model=request.model,
                choices=[],  # 后续填充
                usage=None  # 后续填充
            )

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

                    finish_reason = choice.get("finish_reason", "stop")
                    text = choice.get("text", "")

                    logprobs = choice.get("logprobs", None)
                    completion_choice = CompletionChoice(
                        text=text,
                        index=idx,
                        logprobs=logprobs,
                        finish_reason=finish_reason
                    )
                    choices.append(completion_choice)

            response_obj.choices = choices

            # 计算用量
            from src.llama.models.common.usage import Usage
            prompts = request.prompt if isinstance(request.prompt, list) else [request.prompt]
            prompt_tokens = sum(count_tokens(prompt) for prompt in prompts)
            completion_tokens = sum(count_tokens(choice.text) for choice in choices)
            total_tokens = prompt_tokens + completion_tokens

            response_obj.usage = Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
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
                response_generator = model(
                    prompt=prompt,
                    max_tokens=request.max_tokens or 16,
                    temperature=request.temperature or 1.0,
                    top_p=request.top_p or 1.0,
                    n=request.n or 1,
                    stream=True,  # 流式
                    logprobs=request.logprobs,
                    echo=request.echo or False,
                    stop=request.stop,
                    presence_penalty=request.presence_penalty or 0.0,
                    frequency_penalty=request.frequency_penalty or 0.0,
                    best_of=request.best_of or 1,
                    logit_bias=request.logit_bias
                )
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