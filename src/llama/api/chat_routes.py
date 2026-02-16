from fastapi import APIRouter, Depends, Request
from typing import AsyncGenerator
import asyncio
import time
import logging

from src.llama.models.chat.chat_completion_request import ChatCompletionRequest
from src.llama.models.chat.chat_completion_response import ChatCompletionResponse
from src.llama.models.chat.chat_completion_chunk import ChatCompletionChunk
from src.llama.services.chat_service import ChatService
from src.llama.core.security import (
    verify_api_key,
    get_rate_limiter,
    get_concurrency_controller
)
from src.llama.utils.token_utils import count_tokens_in_messages
from src.llama.exceptions import ValidationError, RateLimitError, ServiceError, AuthenticationError


logger = logging.getLogger(__name__)

router = APIRouter()


def get_chat_service(request: Request) -> ChatService:
    """
    Dependency to get ChatService with the app's config
    """
    config = getattr(request.app.state, 'config', None)
    return ChatService.get_instance(config)


def get_api_key_chat(request: Request):
    return verify_api_key(request=request)


def get_rate_limiter_chat(request: Request):
    return get_rate_limiter(request)


def get_concurrency_controller_chat(request: Request):
    return get_concurrency_controller(request)


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    req: Request,
    service: ChatService = Depends(get_chat_service),
    api_key: str = Depends(get_api_key_chat),
    rate_limiter = Depends(get_rate_limiter_chat),
    concurrency_ctrl = Depends(get_concurrency_controller_chat)
):
    """
    处理聊天生成请求
    """
    client_ip = req.client.host if req.client else "unknown"

    if (not rate_limiter.is_allowed(client_ip)) is True:
        raise RateLimitError("Rate limit exceeded")

    await concurrency_ctrl.acquire()

    try:
        if api_key is None or api_key == "":
            raise AuthenticationError("Unauthorized: Invalid API key")

        # Check if model is loaded via model manager
        model = service.model_manager.get_model()
        if model is None:
            raise ServiceError("Model not loaded")

        total_message_tokens = count_tokens_in_messages(request.messages)

        max_tokens = request.max_tokens or 1000
        total_expected_tokens = total_message_tokens + max_tokens

        if total_expected_tokens > 2048:
            raise ValidationError(
                f"Request exceeds maximum context length. "
                f"Message tokens: {total_message_tokens}, "
                f"Max tokens: {max_tokens}, "
                f"Total: {total_expected_tokens}. "
                f"Maximum allowed: 2048"
            )

        if request.stream:
            async def generate_stream() -> AsyncGenerator[str, None]:
                try:
                    async for chunk in service.generate_stream(request):
                        yield f"data: {chunk.model_dump_json()}\n\n"

                    yield "data: [DONE]\n\n"
                except asyncio.CancelledError:
                    logger.info(f"Stream cancelled for request {request.model}")
                    raise
                except Exception as e:
                    logger.error(f"Stream generation error: {str(e)}")
                    error_chunk = ChatCompletionChunk(
                        id=f"error-{int(time.time())}",
                        object="chat.completion.chunk",
                        created=int(time.time()),
                        model=request.model,
                        choices=[{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "error"
                        }],
                        error=str(e)
                    )
                    yield f"data: {error_chunk.model_dump_json()}\n\n"
                finally:
                    await concurrency_ctrl.release()

            return generate_stream()
        else:
            response = await service.generate(request)
            return response

    except (ValidationError, RateLimitError, ServiceError, AuthenticationError) as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in chat completion request: {str(e)}", exc_info=True)
        raise ServiceError(f"Internal server error: {str(e)}")
    finally:
        if not request.stream:
            await concurrency_ctrl.release()