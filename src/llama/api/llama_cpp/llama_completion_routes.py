"""llama.cpp compatible completion routes."""
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Any, Dict

from src.llama.models.llama_cpp import LlamaCompletionRequest
from src.llama.services.llama_completion_service import LlamaCompletionService
from src.llama.core.security import (
    verify_api_key,
    get_rate_limiter,
    get_concurrency_controller,
)
from src.llama.exceptions import RateLimitError, ServiceError, AuthenticationError
from src.llama.core.logger_manager import logger

router = APIRouter()

SSE_HEADERS: Dict[str, str] = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def get_llama_service(request: Request) -> LlamaCompletionService:
    """Get llama.cpp completion service instance.

    Args:
        request: FastAPI request object.

    Returns:
        LlamaCompletionService instance.
    """
    config = getattr(request.app.state, 'config', None)
    return LlamaCompletionService.get_instance(config)


def get_api_key(request: Request) -> str:
    """Extract and validate API key from request.

    Args:
        request: FastAPI request object.

    Returns:
        Validated API key string.
    """
    return verify_api_key(request=request)


def get_rate_limiter_dep(request: Request) -> Any:
    """Get rate limiter for request."""
    return get_rate_limiter(request)


def get_concurrency_controller_dep(request: Request) -> Any:
    """Get concurrency controller for request."""
    return get_concurrency_controller(request)


async def _validate_request(
    request: LlamaCompletionRequest,
    req: Request,
    api_key: str,
    rate_limiter: Any,
) -> None:
    """Validate completion request.

    Args:
        request: Completion request data.
        req: FastAPI request object.
        api_key: Validated API key.
        rate_limiter: Rate limiter instance.

    Raises:
        RateLimitError: If rate limit exceeded.
        AuthenticationError: If API key invalid.
    """
    client_ip = req.client.host if req.client else "unknown"

    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for client IP: {client_ip}")
        raise RateLimitError("Rate limit exceeded")

    if not api_key:
        logger.warning(f"Authentication failed for client IP: {client_ip}")
        raise AuthenticationError("Unauthorized: Invalid API key")


async def _stream_generator(
    request: LlamaCompletionRequest,
    service: LlamaCompletionService,
    concurrency_ctrl: Any,
) -> Any:
    """Generate SSE stream for completion request.

    Args:
        request: Completion request data.
        service: LlamaCompletionService instance.
        concurrency_ctrl: Concurrency controller instance.

    Yields:
        SSE formatted data strings.
    """
    await concurrency_ctrl.acquire()

    try:
        async for chunk in service.generate_stream(request):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
        error_chunk = {
            "index": 0,
            "content": "",
            "tokens": [],
            "id_slot": -1,
            "stop": True,
            "error": str(e),
        }
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    finally:
        await concurrency_ctrl.release()


@router.post("/completion")
async def llama_completion(
    request: LlamaCompletionRequest,
    req: Request,
    service: LlamaCompletionService = Depends(get_llama_service),
    api_key: str = Depends(get_api_key),
    rate_limiter: Any = Depends(get_rate_limiter_dep),
    concurrency_ctrl: Any = Depends(get_concurrency_controller_dep),
) -> Any:
    """llama.cpp compatible completion endpoint.

    Supports both streaming and non-streaming responses.

    Args:
        request: Completion request data.
        req: FastAPI request object.
        service: LlamaCompletionService instance.
        api_key: Validated API key.
        rate_limiter: Rate limiter instance.
        concurrency_ctrl: Concurrency controller instance.

    Returns:
        StreamingResponse for stream requests, JSON response otherwise.
    """
    await _validate_request(request, req, api_key, rate_limiter)

    if request.stream:
        return StreamingResponse(
            _stream_generator(request, service, concurrency_ctrl),
            media_type="text/event-stream",
            headers=SSE_HEADERS,
        )

    await concurrency_ctrl.acquire()
    try:
        result = await service.generate(request)
        return result
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        raise ServiceError(f"Generation failed: {e}")
    finally:
        await concurrency_ctrl.release()
