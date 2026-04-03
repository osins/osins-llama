"""Completion routes for osins-llama API server.

Provides OpenAI-compatible completion endpoints for text generation.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Any, Dict, List, Optional, Union
import asyncio
import time
import uuid
import json

from llama.models.legacy.completion_request import CompletionRequest
from llama.models.legacy.completion_response import CompletionResponse
from llama.models.common.stream_chunk import StreamChunk
from llama.services.completion_service import CompletionService
from llama.core.security import (
    verify_api_key,
    get_rate_limiter,
    get_concurrency_controller
)
from llama.utils.token_utils import count_tokens
from llama.exceptions import ValidationError, RateLimitError, ServiceError, AuthenticationError
from llama.core.logger_manager import logger

router = APIRouter()

MAX_CONTEXT_LENGTH: int = 2048
DEFAULT_TEMPERATURE: float = 0.8
DEFAULT_TOP_K: int = 40
DEFAULT_TOP_P: float = 0.95
DEFAULT_MIN_P: float = 0.05
DEFAULT_MAX_TOKENS: int = 16
DEFAULT_REPEAT_LAST_N: int = 64
DEFAULT_REPEAT_PENALTY: float = 1.1
SSE_HEADERS: Dict[str, str] = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def get_completion_service(request: Request) -> CompletionService:
    """Get completion service instance from app state.

    Args:
        request: FastAPI request object.

    Returns:
        CompletionService instance.
    """
    logger.info("get_completion_service dependency called")
    config = getattr(request.app.state, 'config', None)
    logger.info(f"Retrieved config from app.state: {config is not None}")
    return CompletionService.get_instance(config)


def get_api_key(request: Request) -> str:
    """Extract and validate API key from request.

    Args:
        request: FastAPI request object.

    Returns:
        Validated API key string.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"get_api_key dependency called, client IP: {client_ip}")
    api_key = verify_api_key(request=request)
    logger.info(f"API key validation passed for client IP: {client_ip}")
    return api_key


def get_rate_limiter_dep(request: Request) -> Any:
    """Get rate limiter for request.

    Args:
        request: FastAPI request object.

    Returns:
        Rate limiter instance.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"get_rate_limiter_dep dependency called for client IP: {client_ip}")
    rate_limiter = get_rate_limiter(request)
    logger.info(f"Rate limiter retrieved for client IP: {client_ip}")
    return rate_limiter


def get_concurrency_controller_dep(request: Request) -> Any:
    """Get concurrency controller for request.

    Args:
        request: FastAPI request object.

    Returns:
        Concurrency controller instance.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"get_concurrency_controller_dep dependency called for client IP: {client_ip}")
    concurrency_ctrl = get_concurrency_controller(request)
    logger.info(f"Concurrency controller retrieved for client IP: {client_ip}")
    return concurrency_ctrl


async def _validate_request(
    request: CompletionRequest,
    req: Request,
    service: CompletionService,
    api_key: str,
    rate_limiter: Any,
) -> None:
    """Validate completion request before processing.

    Args:
        request: Completion request data.
        req: FastAPI request object.
        service: Completion service instance.
        api_key: Validated API key.
        rate_limiter: Rate limiter instance.

    Raises:
        RateLimitError: If rate limit exceeded.
        AuthenticationError: If API key invalid.
        ServiceError: If model not loaded.
        ValidationError: If request exceeds context length.
    """
    client_ip = req.client.host if req.client else "unknown"
    logger.info(f"_validate_request called for model: {request.model}, client IP: {client_ip}")

    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for client IP: {client_ip}")
        raise RateLimitError("Rate limit exceeded")

    if not api_key:
        logger.warning(f"Authentication failed for client IP: {client_ip}")
        raise AuthenticationError("Unauthorized: Invalid API key")

    model = service.model_manager.get_model()
    if model is None:
        logger.error("Model not loaded")
        raise ServiceError("Model not loaded")

    total_prompt_tokens = 0
    if isinstance(request.prompt, str):
        total_prompt_tokens = count_tokens(request.prompt)
    else:
        for p in request.prompt:
            total_prompt_tokens += count_tokens(p)

    logger.info(f"Token validation: prompt tokens={total_prompt_tokens}, max_tokens={request.max_tokens}")

    if request.max_tokens is not None:
        total_expected = total_prompt_tokens + request.max_tokens
        if total_expected > MAX_CONTEXT_LENGTH:
            logger.warning(f"Request exceeds maximum context length: prompt_tokens={total_prompt_tokens}, max_tokens={request.max_tokens}, total={total_expected}")
            raise ValidationError(
                f"Request exceeds maximum context length. "
                f"Prompt tokens: {total_prompt_tokens}, "
                f"Max tokens: {request.max_tokens}, "
                f"Total: {total_expected}. "
                f"Maximum allowed: {MAX_CONTEXT_LENGTH}"
            )

    logger.info(f"All validations passed for model: {request.model}")


async def _stream_tokens(
    service: CompletionService,
    request: CompletionRequest,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream tokens from completion service.

    Args:
        service: Completion service instance.
        request: Completion request data.

    Yields:
        Token chunk dictionaries.
    """
    async for chunk in service.generate_stream(request):
        yield chunk


def _extract_chunk_text(chunk: Dict[str, Any]) -> str:
    """Extract text from chunk safely.

    Args:
        chunk: Token chunk dictionary.

    Returns:
        Extracted text or empty string.
    """
    choices = chunk.get("choices", [])
    if not choices:
        return ""
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return ""
    return first_choice.get("text", "")


def _extract_chunk_index(chunk: Dict[str, Any]) -> int:
    """Extract index from chunk safely.

    Args:
        chunk: Token chunk dictionary.

    Returns:
        Chunk index or 0.
    """
    choices = chunk.get("choices", [])
    if not choices:
        return 0
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return 0
    return first_choice.get("index", 0)


def _build_finish_chunk(
    request_id: str,
    created: int,
    model: str,
    index: int,
    request: CompletionRequest,
) -> Dict[str, Any]:
    """Build finish chunk for stream completion.

    Args:
        request_id: Unique request identifier.
        created: Creation timestamp.
        model: Model name.
        index: Current chunk index.
        request: Original completion request.

    Returns:
        Finish chunk dictionary.
    """
    return {
        "choices": [
            {
                "text": "",
                "index": index,
                "logprobs": None,
                "finish_reason": "length"
            }
        ],
        "created": created,
        "model": model,
        "object": "text_completion",
        "id": request_id
    }


def _build_error_chunk(
    model: str,
    error_message: str,
) -> str:
    """Build error chunk for stream failure.

    Args:
        model: Model name.
        error_message: Error description.

    Returns:
        SSE formatted error chunk.
    """
    error_chunk = StreamChunk(
        id=f"error-{uuid.uuid4().hex[:8]}",
        object="text_completion.chunk",
        created=int(time.time()),
        model=model,
        choices=[{
            "text": "",
            "index": 0,
            "logprobs": None,
            "finish_reason": "error",
        }],
        error=error_message,
    )
    return f"data: {error_chunk.model_dump_json()}\n\n"


async def _stream_generator(
    request: CompletionRequest,
    service: CompletionService,
    concurrency_ctrl: Any,
) -> AsyncGenerator[str, None]:
    """Generate SSE stream for completion request.

    Args:
        request: Completion request data.
        service: Completion service instance.
        concurrency_ctrl: Concurrency controller instance.

    Yields:
        SSE formatted data strings.
    """
    await concurrency_ctrl.acquire()
    request_id = f"cmpl-{uuid.uuid4().hex[:8]}"
    created = int(time.time())
    index = 0
    start_time = time.time()
    model_name = request.model if request.model else service.model_manager.get_model_name()

    try:
        logger.info(f"[{request_id}] Stream start, model: {model_name}, prompt length: {len(request.prompt) if isinstance(request.prompt, str) else len(request.prompt[0])}")

        async for chunk in _stream_tokens(service, request):
            text = _extract_chunk_text(chunk)

            if text:
                logger.info(f"Generated token: {repr(text)} (model: {model_name})")

            sse_data = f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield sse_data
            index = _extract_chunk_index(chunk)

        finish_data = _build_finish_chunk(request_id, created, model_name, index, request)
        finish_message = f"data: {json.dumps(finish_data, ensure_ascii=False)}\n\n"
        yield finish_message

        yield "data: [DONE]\n\n"

        logger.info(f"[{request_id}] Stream finished, total chunks: {index}, elapsed: {time.time()-start_time:.2f}s")

    except asyncio.CancelledError:
        logger.warning(f"[{request_id}] Stream cancelled, elapsed: {time.time()-start_time:.2f}s")
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Stream error: {e}", exc_info=True)
        yield _build_error_chunk(model_name, str(e))
    finally:
        await concurrency_ctrl.release()


def _make_stream_generator(
    request: CompletionRequest,
    service: CompletionService,
    concurrency_ctrl: Any,
) -> AsyncGenerator[str, None]:
    """Create SSE stream generator for completion request.

    Args:
        request: Completion request data.
        service: Completion service instance.
        concurrency_ctrl: Concurrency controller instance.

    Returns:
        AsyncGenerator yielding SSE formatted strings.
    """
    return _stream_generator(request, service, concurrency_ctrl)


async def _handle_non_stream(
    request: CompletionRequest,
    req: Request,
    service: CompletionService,
    api_key: str,
    rate_limiter: Any,
    concurrency_ctrl: Any,
) -> CompletionResponse:
    """Handle non-streaming completion request.

    Args:
        request: Completion request data.
        req: FastAPI request object.
        service: Completion service instance.
        api_key: Validated API key.
        rate_limiter: Rate limiter instance.
        concurrency_ctrl: Concurrency controller instance.

    Returns:
        Completion response.

    Raises:
        HTTPException: On validation or service errors.
        ServiceError: On unexpected errors.
    """
    await _validate_request(request, req, service, api_key, rate_limiter)
    await concurrency_ctrl.acquire()
    try:
        logger.info(f"Starting non-stream generation for model: {request.model}, prompt: {repr(request.prompt[:100] + '...' if len(request.prompt) > 100 else request.prompt) if isinstance(request.prompt, str) else f'{len(request.prompt)} prompts'}")
        start_time = time.time()
        result = await service.generate(request)
        elapsed_time = time.time() - start_time
        total_generated_tokens = 0
        for choice in result.choices:
            if hasattr(choice, 'text'):
                total_generated_tokens += len(choice.text)
            elif isinstance(choice, dict) and 'text' in choice:
                total_generated_tokens += len(choice['text'])
        logger.info(f"Non-stream generation completed for model: {request.model}, tokens generated: {total_generated_tokens}, elapsed time: {elapsed_time:.2f}s")
        return result
    except (ValidationError, RateLimitError, ServiceError, AuthenticationError) as e:
        logger.error(f"Request validation failed: {str(e)}", exc_info=True)
        from fastapi import HTTPException
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise ServiceError(f"Internal server error: {str(e)}")
    finally:
        await concurrency_ctrl.release()


async def _handle_request(
    endpoint_name: str,
    request: CompletionRequest,
    req: Request,
    service: CompletionService,
    api_key: str,
    rate_limiter: Any,
    concurrency_ctrl: Any,
) -> Any:
    """Route completion request to appropriate handler.

    Args:
        endpoint_name: API endpoint name for logging.
        request: Completion request data.
        req: FastAPI request object.
        service: Completion service instance.
        api_key: Validated API key.
        rate_limiter: Rate limiter instance.
        concurrency_ctrl: Concurrency controller instance.

    Returns:
        StreamingResponse for stream requests, CompletionResponse otherwise.

    Raises:
        HTTPException: On validation errors.
    """
    client_ip = req.client.host if req.client else "unknown"
    logger.info(f"Route handler reached for {endpoint_name}, model: {request.model}, client IP: {client_ip}, stream: {request.stream}")
    prompt_length = 0
    if isinstance(request.prompt, str):
        prompt_length = len(request.prompt)
    elif isinstance(request.prompt, list):
        prompt_length = sum(len(p) for p in request.prompt)

    logger.info(f"Request body - ID: {uuid.uuid4().hex[:8]}, Model: {request.model}, Prompt Info: {'provided' if request.prompt else 'missing'}, Prompt Length: {prompt_length}, Body Keys: {list(request.model_dump().keys())}")

    if request.stream:
        try:
            await _validate_request(request, req, service, api_key, rate_limiter)
            logger.info(f"Request validation passed for {endpoint_name}, preparing stream response")
        except (ValidationError, RateLimitError, ServiceError, AuthenticationError) as e:
            logger.error(f"Request validation failed for {endpoint_name}: {str(e)}", exc_info=True)
            from fastapi import HTTPException
            raise HTTPException(status_code=e.status_code, detail=e.message)

        logger.info(f"Returning streaming response for {endpoint_name}, model: {request.model}")
        return StreamingResponse(
            _make_stream_generator(request, service, concurrency_ctrl),
            media_type="text/event-stream",
            headers=SSE_HEADERS,
        )

    logger.info(f"Processing non-stream request for {endpoint_name}, model: {request.model}")
    result = await _handle_non_stream(
        request, req, service, api_key, rate_limiter, concurrency_ctrl
    )
    logger.info(f"Non-stream request completed for {endpoint_name}, model: {request.model}")
    return result


@router.post("/v1/completions", response_model=None)
async def create_completion(
    request: CompletionRequest,
    req: Request,
    service: CompletionService = Depends(get_completion_service),
    api_key: str = Depends(get_api_key),
    rate_limiter: Any = Depends(get_rate_limiter_dep),
    concurrency_ctrl: Any = Depends(get_concurrency_controller_dep),
) -> Any:
    """OpenAI-compatible completions endpoint.

    Args:
        request: Completion request data.
        req: FastAPI request object.
        service: Completion service instance.
        api_key: Validated API key.
        rate_limiter: Rate limiter instance.
        concurrency_ctrl: Concurrency controller instance.

    Returns:
        StreamingResponse for stream requests, CompletionResponse otherwise.
    """
    return await _handle_request(
        "/v1/completions", request, req, service, api_key, rate_limiter, concurrency_ctrl
    )