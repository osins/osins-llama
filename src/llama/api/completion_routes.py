from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import time
import uuid

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
from src.llama.core.logger_manager import logger

router = APIRouter()


# ---------------------------------------------------------------------------
# 依赖注入
# ---------------------------------------------------------------------------

def get_completion_service(request: Request) -> CompletionService:
    logger.info("get_completion_service dependency called")
    config = getattr(request.app.state, 'config', None)
    logger.info(f"Retrieved config from app.state: {config is not None}")
    return CompletionService.get_instance(config)


def get_api_key(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"get_api_key dependency called, client IP: {client_ip}")
    api_key = verify_api_key(request=request)
    logger.info(f"API key validation passed for client IP: {client_ip}")
    return api_key


def get_rate_limiter_dep(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"get_rate_limiter_dep dependency called for client IP: {client_ip}")
    rate_limiter = get_rate_limiter(request)
    logger.info(f"Rate limiter retrieved for client IP: {client_ip}")
    return rate_limiter


def get_concurrency_controller_dep(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"get_concurrency_controller_dep dependency called for client IP: {client_ip}")
    concurrency_ctrl = get_concurrency_controller(request)
    logger.info(f"Concurrency controller retrieved for client IP: {client_ip}")
    return concurrency_ctrl


# ---------------------------------------------------------------------------
# 校验逻辑（流式和非流式共用）
# ---------------------------------------------------------------------------

async def _validate_request(
    request: CompletionRequest,
    req: Request,
    service: CompletionService,
    api_key: str,
    rate_limiter,
):
    """
    执行所有前置校验，不涉及并发控制器。
    校验通过则静默返回，失败则抛出对应异常。
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

    # token 数量校验
    total_prompt_tokens = 0
    if isinstance(request.prompt, str):
        total_prompt_tokens = count_tokens(request.prompt)
    else:
        for p in request.prompt:
            total_prompt_tokens += count_tokens(p)

    logger.info(f"Token validation: prompt tokens={total_prompt_tokens}, max_tokens={request.max_tokens}")

    if request.max_tokens is not None:
        total_expected = total_prompt_tokens + request.max_tokens
        if total_expected > 2048:
            logger.warning(f"Request exceeds maximum context length: prompt_tokens={total_prompt_tokens}, max_tokens={request.max_tokens}, total={total_expected}")
            raise ValidationError(
                f"Request exceeds maximum context length. "
                f"Prompt tokens: {total_prompt_tokens}, "
                f"Max tokens: {request.max_tokens}, "
                f"Total: {total_expected}. "
                f"Maximum allowed: 2048"
            )
    
    logger.info(f"All validations passed for model: {request.model}")


# ---------------------------------------------------------------------------
# 流式生成器工厂（流式请求专用）
# ---------------------------------------------------------------------------

def _make_stream_generator(
    request: CompletionRequest,
    service: CompletionService,
    concurrency_ctrl,
) -> AsyncGenerator[str, None]:
    """
    创建 SSE 流式生成器。
    concurrency_ctrl 在此处 acquire，在 finally 中 release，确保成对出现。
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        # 在生成器内部 acquire，确保与 release 成对
        await concurrency_ctrl.acquire()
        logger.info(f"Starting stream generation for model: {request.model}, prompt: {repr(request.prompt[:100] + '...' if len(request.prompt) > 100 else request.prompt) if isinstance(request.prompt, str) else f'{len(request.prompt)} prompts'}")
        start_time = time.time()
        total_tokens = 0
        try:
            async for chunk in service.generate_stream(request):
                # 记录每个生成的token/文本片段
                text = ""
                try:
                    if isinstance(chunk.choices[0], dict):
                        text = chunk.choices[0].get("text", "")
                    else:
                        text = getattr(chunk.choices[0], 'text', '')
                except (IndexError, AttributeError):
                    pass
                    
                if text:
                    total_tokens += len(text)
                    logger.info(f"Generated token: {repr(text)} (model: {request.model})")
                yield f"data: {chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"
            elapsed_time = time.time() - start_time
            logger.info(f"Stream generation completed for model: {request.model}, total tokens: {total_tokens}, elapsed time: {elapsed_time:.2f}s")

        except asyncio.CancelledError:
            elapsed_time = time.time() - start_time
            logger.info(f"Stream cancelled for request {request.model}, total tokens: {total_tokens}, elapsed time: {elapsed_time:.2f}s")
            raise
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Stream generation error: {str(e)}, model: {request.model}, total tokens: {total_tokens}, elapsed time: {elapsed_time:.2f}s")
            error_chunk = StreamChunk(
                id=f"error-{uuid.uuid4().hex[:8]}",
                object="text_completion.chunk",
                created=int(time.time()),
                model=request.model,
                choices=[{
                    "text": "",
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "error",
                }],
                error=str(e),
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"
        finally:
            await concurrency_ctrl.release()

    return generate_stream()


# ---------------------------------------------------------------------------
# 非流式处理（共用逻辑）
# ---------------------------------------------------------------------------

async def _handle_non_stream(
    request: CompletionRequest,
    req: Request,
    service: CompletionService,
    api_key: str,
    rate_limiter,
    concurrency_ctrl,
):
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


# ---------------------------------------------------------------------------
# 路由处理
# ---------------------------------------------------------------------------

async def _handle_request(
    endpoint_name: str,
    request: CompletionRequest,
    req: Request,
    service: CompletionService,
    api_key: str,
    rate_limiter,
    concurrency_ctrl,
):
    client_ip = req.client.host if req.client else "unknown"
    logger.info(f"Route handler reached for {endpoint_name}, model: {request.model}, client IP: {client_ip}, stream: {request.stream}")
    prompt_length = 0
    if isinstance(request.prompt, str):
        prompt_length = len(request.prompt)
    elif isinstance(request.prompt, list):
        prompt_length = sum(len(p) for p in request.prompt)
    
    logger.info(f"Request body - ID: {uuid.uuid4().hex[:8]}, Model: {request.model}, Prompt Info: {'provided' if request.prompt else 'missing'}, Prompt Length: {prompt_length}, Body Keys: {list(request.model_dump().keys())}")

    if request.stream:
        # 流式：先做校验（不 acquire），校验通过后返回 StreamingResponse
        # StreamingResponse 内部的生成器负责 acquire/release
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
        )
    else:
        logger.info(f"Processing non-stream request for {endpoint_name}, model: {request.model}")
        result = await _handle_non_stream(
            request, req, service, api_key, rate_limiter, concurrency_ctrl
        )
        logger.info(f"Non-stream request completed for {endpoint_name}, model: {request.model}")
        return result


@router.post("/v1/completions")
async def create_completion(
    request: CompletionRequest,
    req: Request,
    service: CompletionService = Depends(get_completion_service),
    api_key: str = Depends(get_api_key),
    rate_limiter=Depends(get_rate_limiter_dep),
    concurrency_ctrl=Depends(get_concurrency_controller_dep),
):
    return await _handle_request(
        "/v1/completions", request, req, service, api_key, rate_limiter, concurrency_ctrl
    )


@router.post("/completion")
async def legacy_completion(
    request: CompletionRequest,
    req: Request,
    service: CompletionService = Depends(get_completion_service),
    api_key: str = Depends(get_api_key),
    rate_limiter=Depends(get_rate_limiter_dep),
    concurrency_ctrl=Depends(get_concurrency_controller_dep),
):
    return await _handle_request(
        "/completion", request, req, service, api_key, rate_limiter, concurrency_ctrl
    )