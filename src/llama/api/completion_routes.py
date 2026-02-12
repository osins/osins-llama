from fastapi import APIRouter, Depends, Request
from typing import AsyncGenerator
import asyncio
import time
import logging

from src.llama.models.legacy.completion_request import CompletionRequest
from src.llama.models.legacy.completion_response import CompletionResponse
from src.llama.models.common.stream_chunk import StreamChunk
from src.llama.services.completion_service import CompletionService
from src.llama.core.security import (
    verify_api_key,
    get_rate_limiter,
    get_concurrency_controller
)
from src.llama.utils.token_utils import count_tokens
from src.llama.exceptions import ValidationError, RateLimitError, ServiceError, AuthenticationError


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/v1/completions", response_model=CompletionResponse)
async def create_completion(
    request: CompletionRequest,
    req: Request,
    service: CompletionService = Depends(CompletionService.get_instance),
    api_key: str = Depends(verify_api_key),
    rate_limiter = Depends(get_rate_limiter),
    concurrency_ctrl = Depends(get_concurrency_controller)
):
    """
    处理文本生成请求
    """
    client_ip = req.client.host if req.client else "unknown"

    if (not rate_limiter.is_allowed(client_ip)) is True:
        raise RateLimitError("Rate limit exceeded")

    await concurrency_ctrl.acquire()

    try:
        if api_key is None or api_key == "":
            raise AuthenticationError("Unauthorized: Invalid API key")

        if (not hasattr(service, 'model') or service.model is None) is True:
            raise ServiceError("Model not loaded")

        total_prompt_tokens = 0
        if isinstance(request.prompt, str):
            prompt_tokens = count_tokens(request.prompt)
            total_prompt_tokens = prompt_tokens
        else:
            for prompt in request.prompt:
                prompt_tokens = count_tokens(prompt)
                total_prompt_tokens += prompt_tokens

        if request.max_tokens is not None:
            total_expected_tokens = total_prompt_tokens + request.max_tokens
            if total_expected_tokens > 2048:
                raise ValidationError(
                    f"Request exceeds maximum context length. "
                    f"Prompt tokens: {total_prompt_tokens}, "
                    f"Max tokens: {request.max_tokens}, "
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
                    error_chunk = StreamChunk(
                        id=f"error-{int(time.time())}",
                        object="text_completion.chunk",
                        created=int(time.time()),
                        model=request.model,
                        choices=[{
                            "text": "",
                            "index": 0,
                            "logprobs": None,
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
        logger.error(f"Unexpected error in completion request: {str(e)}", exc_info=True)
        raise ServiceError(f"Internal server error: {str(e)}")
    finally:
        if not request.stream:
            await concurrency_ctrl.release()