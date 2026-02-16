from typing import AsyncGenerator
from fastapi import Request
from src.llama.models.chat.chat_completion_request import ChatCompletionRequest
from src.llama.models.chat.chat_completion_response import ChatCompletionResponse
from src.llama.models.chat.chat_completion_chunk import ChatCompletionChunk
from src.llama.core.model_manager import ModelManager
from src.llama.config.config import Config
from src.llama.utils.token_utils import count_tokens_in_messages
import asyncio
import time
import uuid
from src.llama.exceptions import ServiceError


class ChatService:
    """
    Chat服务类
    处理聊天生成请求，包括流式和非流式响应
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
        获取ChatService单例实例
        """
        if cls._instance is None:
            cls._instance = cls(config)
        elif config is not None:
            # If a config is provided and instance already exists, update the config
            cls._instance.config = config
        return cls._instance

    def _validate_request(self, request: ChatCompletionRequest):
        """
        验证请求参数

        Args:
            request: ChatCompletion请求对象

        Raises:
            ValueError: 参数验证失败时抛出
        """
        # 验证模型名称
        if not request.model or len(request.model.strip()) == 0:
            raise ValueError("Model name is required")

        # 验证消息列表
        if not request.messages or len(request.messages) == 0:
            raise ValueError("Messages are required")

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

    async def generate(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        生成非流式响应

        Args:
            request: ChatCompletion请求对象

        Returns:
            ChatCompletionResponse: 完整的响应对象
        """
        from src.llama.core.logger_manager import logger
        logger.info(f"ChatService.generate called for model: {request.model}, messages count: {len(request.messages)}")

        try:
            # 验证请求参数
            self._validate_request(request)

            # 获取模型实例
            model = self.model_manager.get_model()
            if model is None:
                raise ServiceError("Model not loaded")

            # 检查token数量
            total_tokens = count_tokens_in_messages(request.messages)
            if total_tokens > self.config.resources.max_prompt_tokens:
                raise ValueError(f"Messages exceed maximum token count: {self.config.resources.max_prompt_tokens}")

            # 生成响应
            start_time = time.time()

            # 将消息转换为适合模型的格式
            formatted_messages = self._format_messages(request.messages)

            try:
                # 构建模型调用参数字典
                raw_kwargs = {
                    "prompt": formatted_messages,
                    "max_tokens": request.max_tokens or 1000,
                    "temperature": request.temperature or 0.7,
                    "top_p": request.top_p or 1.0,
                    "stream": False,  # 非流式
                    "stop": request.stop,
                    "presence_penalty": request.presence_penalty or 0.0,
                    "frequency_penalty": request.frequency_penalty or 0.0
                }

                # 应用参数过滤
                from src.llama.core.model_manager import filter_llama_params
                model_kwargs = filter_llama_params(raw_kwargs)
                
                # 降低 temperature 以提高生成稳定性
                if "temperature" not in model_kwargs or model_kwargs["temperature"] > 1.0:
                    model_kwargs["temperature"] = 1.0  # 从更高值降低到1.0

                # 记录开始生成的时间
                gen_start_time = time.time()
                logger.info(f"Starting non-stream chat generation for params: {list(model_kwargs.keys())}")

                # 生成响应
                response = model(**model_kwargs)

                # 记录生成完成的时间
                elapsed_time = time.time() - gen_start_time
                logger.info(f"Non-stream chat generation completed, elapsed time: {elapsed_time:.2f}s")

                # 验证响应格式
                if not isinstance(response, dict) or "choices" not in response:
                    raise ServiceError("Invalid model response format")
            except Exception as e:
                logger.error(f"ChatService.generate error: {e}", exc_info=True)
                raise ServiceError(f"Model generation failed: {str(e)}")

            # 构造响应对象
            response_obj = ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex}",
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

                    # 创建选择项
                    from src.llama.models.chat.chat_completion_choice import ChatCompletionChoice
                    from src.llama.models.chat.chat_message import ChatMessage
                    from src.llama.models.chat.chat_role import ChatRole

                    message_content = choice.get("message", {}).get("content", "")
                    finish_reason = choice.get("finish_reason", "stop")

                    chat_message = ChatMessage(
                        role=ChatRole.ASSISTANT,
                        content=message_content
                    )

                    chat_choice = ChatCompletionChoice(
                        index=idx,
                        message=chat_message,
                        finish_reason=finish_reason
                    )

                    choices.append(chat_choice)

            response_obj.choices = choices

            # 计算用量
            from src.llama.models.common.usage import Usage
            prompt_tokens = count_tokens_in_messages(request.messages)
            completion_tokens = sum(
                count_tokens_in_messages([choice.message]) for choice in choices
            )
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

    async def generate_stream(self, request: ChatCompletionRequest) -> AsyncGenerator[ChatCompletionChunk, None]:
        """
        生成流式响应

        Args:
            request: ChatCompletion请求对象

        Yields:
            ChatCompletionChunk: 流式数据块
        """
        from src.llama.core.logger_manager import logger
        logger.info(f"ChatService.generate_stream called for model: {request.model}, messages count: {len(request.messages)}")

        try:
            # 验证请求参数
            self._validate_request(request)

            # 获取模型实例
            model = self.model_manager.get_model()
            if model is None:
                raise ServiceError("Model not loaded")

            # 检查token数量
            total_tokens = count_tokens_in_messages(request.messages)
            if total_tokens > self.config.resources.max_prompt_tokens:
                raise ValueError(f"Messages exceed maximum token count: {self.config.resources.max_prompt_tokens}")

            # 将消息转换为适合模型的格式
            formatted_messages = self._format_messages(request.messages)

            try:
                # 构建模型调用参数字典
                raw_kwargs = {
                    "prompt": formatted_messages,
                    "max_tokens": request.max_tokens or 1000,
                    "temperature": request.temperature or 0.7,
                    "top_p": request.top_p or 1.0,
                    "stream": True,  # 流式
                    "stop": request.stop,
                    "presence_penalty": request.presence_penalty or 0.0,
                    "frequency_penalty": request.frequency_penalty or 0.0
                }

                # 应用参数过滤
                from src.llama.core.model_manager import filter_llama_params
                model_kwargs = filter_llama_params(raw_kwargs)
                
                # 降低 temperature 以提高生成稳定性
                if "temperature" not in model_kwargs or model_kwargs["temperature"] > 1.0:
                    model_kwargs["temperature"] = 1.0  # 从更高值降低到1.0

                # 记录开始生成的时间
                gen_start_time = time.time()
                logger.info(f"Starting stream chat generation for params: {list(model_kwargs.keys())}")

                # 生成流式响应
                response_generator = model(**model_kwargs)

                # 记录生成完成的时间
                elapsed_time = time.time() - gen_start_time
                logger.info(f"Stream chat generation setup completed, elapsed time: {elapsed_time:.2f}s")
            except Exception as e:
                logger.error(f"ChatService.generate_stream error during generation: {e}", exc_info=True)
                raise ServiceError(f"Model generation failed: {str(e)}")

            # 生成ID
            gen_id = f"chatcmpl-{uuid.uuid4().hex}"
            created_time = int(time.time())

            # 模拟流式输出
            full_content = ""
            try:
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

                        delta_content = choice.get("delta", {}).get("content", "")
                        full_content += delta_content

                        # 创建流式数据块
                        from src.llama.models.chat.chat_completion_chunk import ChatCompletionChunk
                        from src.llama.models.chat.chat_completion_chunk_choice import ChatCompletionChunkChoice
                        from src.llama.models.chat.chat_completion_delta import ChatCompletionDelta

                        delta = ChatCompletionDelta(content=delta_content, role="assistant")

                        chunk_choice = ChatCompletionChunkChoice(
                            index=0,
                            delta=delta,
                            finish_reason=None
                        )

                        stream_chunk = ChatCompletionChunk(
                            id=gen_id,
                            object="chat.completion.chunk",
                            created=created_time,
                            model=request.model,
                            choices=[chunk_choice]
                        )

                        yield stream_chunk
            except Exception as e:
                logger.error(f"Error during stream processing: {e}", exc_info=True)
                raise ServiceError(f"Stream processing failed: {str(e)}")

            # 发送结束块
            end_chunk = ChatCompletionChunk(
                id=gen_id,
                object="chat.completion.chunk",
                created=created_time,
                model=request.model,
                choices=[
                    {
                        "index": 0,
                        "delta": {},
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
            logger.error(f"ChatService.generate_stream error: {e}", exc_info=True)
            raise ServiceError(f"Unexpected error during streaming: {str(e)}")

    def _format_messages(self, messages):
        """
        将消息格式化为模型可接受的格式

        Args:
            messages: 消息列表

        Returns:
            格式化后的消息字符串
        """
        formatted = ""
        for msg in messages:
            role = getattr(msg, 'role', 'user')
            content = getattr(msg, 'content', '')
            formatted += f"{role}: {content}\n"
        formatted += "assistant:"
        return formatted