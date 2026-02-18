"""llama.cpp compatible completion service.

Implements the complete llama.cpp server /completion API specification.
"""
import time
import threading
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional, List
from pathlib import Path

from src.llama.models.llama_cpp import (
    LlamaCompletionRequest,
    GenerationSettings,
    Timings,
)
from src.llama.core.model_manager import ModelManager
from src.llama.config.config import Config
from src.llama.exceptions.service_error import ServiceError
from src.llama.core.logger_manager import logger


LLAMA_CPP_PARAMS = {
    "suffix", "max_tokens", "temperature", "top_p", "min_p", "typical_p",
    "logprobs", "echo", "stop", "frequency_penalty", "presence_penalty",
    "repeat_penalty", "top_k", "stream", "seed", "tfs_z", "mirostat_mode",
    "mirostat_tau", "mirostat_eta", "grammar", "logit_bias",
}

PARAM_ALIAS_MAP = {
    "max_new_tokens": "max_tokens",
    "n_predict": "max_tokens",
    "num_predict": "max_tokens",
    "repetition_penalty": "repeat_penalty",
    "rep_pen": "repeat_penalty",
    "stopping_strings": "stop",
    "mirostat": "mirostat_mode",
    "tfs": "tfs_z",
    "ban_eos_token": "ignore_eos",
    "rep_pen_range": "repeat_last_n",
}


class SlotManager:
    """Manages inference slots for concurrent requests."""

    def __init__(self, max_slots: int = 8):
        self._max_slots = max_slots
        self._slots: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._next_id = 0

    def acquire_slot(self) -> int:
        """Acquire an available slot.

        Returns:
            Slot ID.
        """
        with self._lock:
            for slot_id in range(self._max_slots):
                if slot_id not in self._slots:
                    self._slots[slot_id] = {
                        "acquired_at": time.time(),
                        "status": "busy",
                    }
                    return slot_id
            return -1

    def release_slot(self, slot_id: int) -> None:
        """Release a slot.

        Args:
            slot_id: Slot ID to release.
        """
        with self._lock:
            if slot_id in self._slots:
                del self._slots[slot_id]

    def get_slot_info(self, slot_id: int) -> Dict[str, Any]:
        """Get slot information.

        Args:
            slot_id: Slot ID.

        Returns:
            Slot information dictionary.
        """
        with self._lock:
            return self._slots.get(slot_id, {})


def _build_llama_params(request: LlamaCompletionRequest) -> Dict[str, Any]:
    """Build llama-cpp-python parameters from request.

    Args:
        request: LlamaCompletionRequest instance.

    Returns:
        Dictionary of parameters for llama-cpp-python.
    """
    raw_params = request.model_dump(exclude_none=True)
    logger.debug(f"[LLAMA_CPP] Raw request params: {raw_params}")

    params: Dict[str, Any] = {}

    for key, value in raw_params.items():
        target = PARAM_ALIAS_MAP.get(key, key)

        if target == "max_tokens" and "max_tokens" in params:
            params["max_tokens"] = max(params["max_tokens"], value)
        elif target == "repeat_penalty" and "repeat_penalty" in params:
            params["repeat_penalty"] = max(params["repeat_penalty"], value)
        elif target == "stop" and "stop" in params:
            existing = params["stop"] if isinstance(params["stop"], list) else [params["stop"]]
            new_val = value if isinstance(value, list) else [value]
            merged = list(dict.fromkeys(existing + new_val))
            params["stop"] = merged
        else:
            params[target] = value

    filtered = {k: v for k, v in params.items() if k in LLAMA_CPP_PARAMS}

    removed_keys = set(params.keys()) - set(filtered.keys())
    if removed_keys:
        logger.debug(f"[LLAMA_CPP] Filtered out params (not in whitelist): {removed_keys}")

    if "grammar" in filtered:
        grammar_val = filtered["grammar"]
        if grammar_val is not None and not isinstance(grammar_val, str):
            del filtered["grammar"]
        if grammar_val == "":
            del filtered["grammar"]

    if "logit_bias" in filtered:
        lb = filtered["logit_bias"]
        if not lb:
            del filtered["logit_bias"]
        elif isinstance(lb, list):
            if len(lb) == 0:
                del filtered["logit_bias"]
            else:
                try:
                    filtered["logit_bias"] = {int(item[0]): item[1] for item in lb}
                except Exception:
                    del filtered["logit_bias"]

    if "stop" in filtered:
        stop_val = filtered["stop"]
        if isinstance(stop_val, list):
            cleaned = list(dict.fromkeys(s for s in stop_val if s))
            if cleaned:
                filtered["stop"] = cleaned
            else:
                del filtered["stop"]
        elif not stop_val:
            del filtered["stop"]

    logger.debug(f"[LLAMA_CPP] Final filtered params: {filtered}")
    return filtered


def _build_full_generation_settings(
    request: LlamaCompletionRequest,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """Build complete generation settings for llama.cpp response.

    Args:
        request: Original request.
        params: Processed parameters.

    Returns:
        Dictionary with all generation settings.
    """
    stop_list = params.get("stop", [])
    if isinstance(stop_list, str):
        stop_list = [stop_list]

    dry_breakers = request.dry_sequence_breakers
    if dry_breakers is None:
        dry_breakers = ["\n", ":", "\"", "*"]

    samplers = request.samplers
    if samplers is None:
        samplers = ["penalties", "dry", "top_n_sigma", "top_k", "typ_p", "top_p", "min_p", "xtc", "temperature"]

    return {
        "seed": request.seed if request.seed is not None else -1,
        "temperature": params.get("temperature", 0.8),
        "dynatemp_range": 0.0,
        "dynatemp_exponent": 1.0,
        "top_k": params.get("top_k", 40),
        "top_p": params.get("top_p", 0.95),
        "min_p": request.min_p if request.min_p is not None else 0.05,
        "top_n_sigma": -1.0,
        "xtc_probability": request.xtc_probability if request.xtc_probability is not None else 0.0,
        "xtc_threshold": request.xtc_threshold if request.xtc_threshold is not None else 0.1,
        "typical_p": request.typical_p if request.typical_p is not None else 1.0,
        "repeat_last_n": request.repeat_last_n if request.repeat_last_n is not None else 64,
        "repeat_penalty": params.get("repeat_penalty", 1.0),
        "presence_penalty": request.presence_penalty if request.presence_penalty is not None else 0.0,
        "frequency_penalty": request.frequency_penalty if request.frequency_penalty is not None else 0.0,
        "dry_multiplier": request.dry_multiplier if request.dry_multiplier is not None else 0.0,
        "dry_base": request.dry_base if request.dry_base is not None else 1.75,
        "dry_allowed_length": request.dry_allowed_length if request.dry_allowed_length is not None else 2,
        "dry_penalty_last_n": request.dry_penalty_last_n if request.dry_penalty_last_n is not None else -1,
        "dry_sequence_breakers": dry_breakers,
        "mirostat": request.mirostat if request.mirostat is not None else 0,
        "mirostat_tau": request.mirostat_tau if request.mirostat_tau is not None else 5.0,
        "mirostat_eta": request.mirostat_eta if request.mirostat_eta is not None else 0.1,
        "penalize_nl": True,
        "stop": stop_list,
        "max_tokens": params.get("max_tokens", -1),
        "n_predict": params.get("max_tokens", -1),
        "n_keep": request.n_keep if request.n_keep is not None else 0,
        "n_discard": request.n_discard if request.n_discard is not None else 0,
        "ignore_eos": request.ignore_eos if request.ignore_eos is not None else False,
        "stream": request.stream if request.stream is not None else False,
        "logit_bias": [],
        "n_probs": request.n_probs if request.n_probs is not None else 0,
        "min_keep": request.min_keep if request.min_keep is not None else 0,
        "grammar": request.grammar if request.grammar else "",
        "grammar_lazy": request.grammar_lazy if request.grammar_lazy is not None else False,
        "grammar_triggers": [],
        "preserved_tokens": [],
        "chat_format": "Content-only",
        "reasoning_format": "deepseek",
        "reasoning_in_content": False,
        "thinking_forced_open": False,
        "samplers": samplers,
        "speculative.n_max": 16,
        "speculative.n_min": 0,
        "speculative.p_min": 0.75,
        "speculative.type": "none",
        "speculative.ngram_size_n": 1024,
        "speculative.ngram_size_m": 1024,
        "speculative.ngram_m_hits": 1024,
        "timings_per_token": request.timings_per_token if request.timings_per_token is not None else False,
        "post_sampling_probs": request.post_sampling_probs if request.post_sampling_probs is not None else False,
        "backend_sampling": False,
        "lora": [],
    }


def _check_stop_condition(text: str, stop_sequences: List[str]) -> tuple:
    """Check if text matches any stop sequence.

    Args:
        text: Generated text.
        stop_sequences: List of stop sequences.

    Returns:
        Tuple of (should_stop, stop_type, stopping_word).
    """
    if not stop_sequences:
        return False, "", ""

    for stop_seq in stop_sequences:
        if stop_seq and stop_seq in text:
            return True, "stop", stop_seq

    return False, "", ""


class LlamaCompletionService:
    """llama.cpp compatible completion service.

    Provides completion generation with llama.cpp server compatible output format.
    Supports concurrent requests with independent slots.
    """

    _instance: Optional["LlamaCompletionService"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, config: Config):
        self.config = config
        self.model_manager = ModelManager.get_instance(config)
        self.slot_manager = SlotManager(
            max_slots=config.security.max_concurrent_requests if config else 8
        )

    @classmethod
    def get_instance(cls, config: Config = None) -> "LlamaCompletionService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    def _get_model_name(self) -> str:
        """Get loaded model name."""
        return self.model_manager.get_model_name()

    def _count_prompt_tokens(self, model: Any, prompt: str, add_bos: bool) -> int:
        """Count tokens in prompt.

        Args:
            model: Llama model instance.
            prompt: Input prompt.
            add_bos: Whether to add BOS token.

        Returns:
            Number of tokens.
        """
        try:
            if hasattr(model, 'tokenize'):
                tokens = model.tokenize(prompt.encode('utf-8'), add_bos=add_bos)
                return len(tokens)
        except Exception:
            pass
        return len(prompt.split())

    async def generate_stream(
        self,
        request: LlamaCompletionRequest,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming completion in llama.cpp format.

        Each token chunk contains:
        - index: token sequence number
        - content: generated text for this token
        - tokens: token ID array
        - stop: whether stop condition triggered
        - id_slot: slot ID for this request
        - tokens_predicted: total tokens predicted so far
        - tokens_evaluated: prompt tokens evaluated

        Final chunk contains complete generation_settings and timings.

        Args:
            request: LlamaCompletionRequest instance.

        Yields:
            Dictionary chunks in llama.cpp format.
        """
        model_name = self._get_model_name()
        logger.info(f"[LLAMA_CPP] generate_stream START | model: {model_name}")

        model = self.model_manager.get_model()
        if model is None:
            raise ServiceError("Model not loaded")

        prompt = request.prompt if isinstance(request.prompt, str) else (
            request.prompt[0] if request.prompt else ""
        )

        if not prompt:
            raise ServiceError("Prompt cannot be empty")

        params = _build_llama_params(request)
        params["stream"] = True

        if "temperature" in params and params["temperature"] > 1.0:
            params["temperature"] = 1.0

        stop_sequences = params.get("stop", [])
        if isinstance(stop_sequences, str):
            stop_sequences = [stop_sequences]

        slot_id = request.id_slot if request.id_slot is not None and request.id_slot >= 0 else -1

        add_bos = request.add_bos_token if request.add_bos_token is not None else True
        prompt_tokens = self._count_prompt_tokens(model, prompt, add_bos)

        logger.info(f"[LLAMA_CPP] Request params: {params}")
        logger.info(f"[LLAMA_CPP] Prompt tokens: {prompt_tokens}, slot_id: {slot_id}")
        logger.info(f"[LLAMA_CPP] Prompt preview: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")

        generation_settings = _build_full_generation_settings(request, params)

        tokens_predicted = 0
        full_content = ""
        start_time = time.time()
        prompt_start = time.time()
        prompt_ms = 0.0

        token_timings: List[float] = []
        last_token_time = start_time

        try:
            prompt_ms = (time.time() - prompt_start) * 1000
            logger.info(f"[LLAMA_CPP] Calling model() with stream=True")

            for chunk in model(prompt, **params):
                if isinstance(chunk, dict):
                    choices = chunk.get("choices", [])
                    if choices:
                        text = choices[0].get("text", "")
                    else:
                        text = ""
                    logger.debug(f"[LLAMA_CPP] Raw chunk from model: {chunk}")
                else:
                    text = str(chunk)
                    logger.debug(f"[LLAMA_CPP] Raw chunk (non-dict): {chunk}")

                if text:
                    full_content += text
                    current_time = time.time()
                    token_time_ms = (current_time - last_token_time) * 1000
                    token_timings.append(token_time_ms)
                    last_token_time = current_time

                    should_stop, stop_type, stopping_word = _check_stop_condition(
                        full_content, stop_sequences
                    )

                    token_ids = []
                    try:
                        if hasattr(model, 'tokenize'):
                            token_ids = list(model.tokenize(text.encode('utf-8'), add_bos=False))
                    except Exception:
                        pass

                    token_chunk = {
                        "index": 0,
                        "content": text,
                        "tokens": token_ids,
                        "id_slot": slot_id,
                        "stop": should_stop,
                        "model": model_name,
                        "tokens_predicted": tokens_predicted + 1,
                        "tokens_evaluated": prompt_tokens,
                    }

                    logger.debug(f"[LLAMA_CPP] Token #{tokens_predicted + 1}: '{text}' | token_ids: {token_ids} | time: {token_time_ms:.2f}ms")

                    if request.timings_per_token and request.timings_per_token:
                        token_chunk["timings"] = {
                            "prompt_n": prompt_tokens,
                            "prompt_ms": prompt_ms,
                            "predicted_n": tokens_predicted + 1,
                            "predicted_ms": sum(token_timings),
                        }

                    yield token_chunk
                    tokens_predicted += 1

                    if should_stop:
                        break

            elapsed_ms = (time.time() - start_time) * 1000

            final_stop_type = "limit"
            final_stopping_word = ""
            should_stop, stop_type, stopping_word = _check_stop_condition(
                full_content, stop_sequences
            )
            if should_stop:
                final_stop_type = stop_type
                final_stopping_word = stopping_word

            logger.info(f"[LLAMA_CPP] Stream FINISHED | tokens: {tokens_predicted} | elapsed: {elapsed_ms/1000:.2f}s | stop_type: {final_stop_type}")
            logger.info(f"[LLAMA_CPP] Full content: {full_content[:500]}{'...' if len(full_content) > 500 else ''}")

            finish_chunk = {
                "index": 0,
                "content": "",
                "tokens": [],
                "id_slot": slot_id,
                "stop": True,
                "model": model_name,
                "tokens_predicted": tokens_predicted,
                "tokens_evaluated": prompt_tokens,
                "generation_settings": generation_settings,
                "prompt": prompt,
                "has_new_line": "\n" in full_content,
                "truncated": False,
                "stop_type": final_stop_type,
                "stopping_word": final_stopping_word,
                "tokens_cached": tokens_predicted,
                "timings": {
                    "cache_n": 0,
                    "prompt_n": prompt_tokens,
                    "prompt_ms": prompt_ms,
                    "prompt_per_token_ms": prompt_ms / max(prompt_tokens, 1),
                    "prompt_per_second": 1000.0 * prompt_tokens / max(prompt_ms, 1),
                    "predicted_n": tokens_predicted,
                    "predicted_ms": elapsed_ms,
                    "predicted_per_token_ms": elapsed_ms / max(tokens_predicted, 1),
                    "predicted_per_second": 1000.0 * tokens_predicted / max(elapsed_ms, 1),
                },
            }
            yield finish_chunk

            logger.info(f"[LLAMA_CPP] Stream completed, slot: {slot_id}, tokens: {tokens_predicted}, elapsed: {elapsed_ms/1000:.2f}s")

        except Exception as e:
            logger.error(f"Stream generation error: {e}", exc_info=True)
            raise ServiceError(f"Generation failed: {e}")

    async def generate(
        self,
        request: LlamaCompletionRequest,
    ) -> Dict[str, Any]:
        """Generate non-streaming completion in llama.cpp format.

        Returns complete response with:
        - content: full generated text
        - generation_settings: all sampling parameters
        - timings: complete timing information
        - stop_type and stopping_word if stopped early

        Args:
            request: LlamaCompletionRequest instance.

        Returns:
            Dictionary in llama.cpp format.
        """
        model_name = self._get_model_name()
        logger.info(f"[LLAMA_CPP] generate (non-stream) START | model: {model_name}")

        model = self.model_manager.get_model()
        if model is None:
            raise ServiceError("Model not loaded")

        prompt = request.prompt if isinstance(request.prompt, str) else (
            request.prompt[0] if request.prompt else ""
        )

        if not prompt:
            raise ServiceError("Prompt cannot be empty")

        params = _build_llama_params(request)
        params["stream"] = False

        if "temperature" in params and params["temperature"] > 1.0:
            params["temperature"] = 1.0

        stop_sequences = params.get("stop", [])
        if isinstance(stop_sequences, str):
            stop_sequences = [stop_sequences]

        slot_id = request.id_slot if request.id_slot is not None and request.id_slot >= 0 else -1

        add_bos = request.add_bos_token if request.add_bos_token is not None else True
        prompt_tokens = self._count_prompt_tokens(model, prompt, add_bos)

        logger.info(f"[LLAMA_CPP] Request params: {params}")
        logger.info(f"[LLAMA_CPP] Prompt tokens: {prompt_tokens}, slot_id: {slot_id}")
        logger.info(f"[LLAMA_CPP] Prompt preview: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")

        generation_settings = _build_full_generation_settings(request, params)

        start_time = time.time()
        prompt_start = time.time()
        prompt_ms = 0.0

        try:
            prompt_ms = (time.time() - prompt_start) * 1000
            logger.info(f"[LLAMA_CPP] Calling model() with stream=False")

            result = model(prompt, **params)
            logger.debug(f"[LLAMA_CPP] Raw result from model: {result}")
        except Exception as e:
            logger.error(f"[LLAMA_CPP] Generation error: {e}", exc_info=True)
            raise ServiceError(f"Generation failed: {e}")

        elapsed_ms = (time.time() - start_time) * 1000

        if isinstance(result, dict):
            choices = result.get("choices", [])
            if choices:
                content = choices[0].get("text", "")
            else:
                content = ""
            usage = result.get("usage", {})
            tokens_predicted = usage.get("completion_tokens", 0)
            if tokens_predicted == 0 and content:
                tokens_predicted = self._count_prompt_tokens(model, content, False)
        else:
            content = str(result)
            tokens_predicted = self._count_prompt_tokens(model, content, False)

        final_stop_type = "limit"
        final_stopping_word = ""
        should_stop, stop_type, stopping_word = _check_stop_condition(
            content, stop_sequences
        )
        if should_stop:
            final_stop_type = stop_type
            final_stopping_word = stopping_word

        logger.info(f"[LLAMA_CPP] Generation FINISHED | tokens: {tokens_predicted} | elapsed: {elapsed_ms/1000:.2f}s | stop_type: {final_stop_type}")
        logger.info(f"[LLAMA_CPP] Generated content: {content[:500]}{'...' if len(content) > 500 else ''}")

        response = {
            "index": 0,
            "content": content,
            "tokens": [],
            "id_slot": slot_id,
            "stop": True,
            "model": model_name,
            "tokens_predicted": tokens_predicted,
            "tokens_evaluated": prompt_tokens,
            "generation_settings": generation_settings,
            "prompt": prompt,
            "has_new_line": "\n" in content,
            "truncated": False,
            "stop_type": final_stop_type,
            "stopping_word": final_stopping_word,
            "tokens_cached": tokens_predicted,
            "timings": {
                "cache_n": 0,
                "prompt_n": prompt_tokens,
                "prompt_ms": prompt_ms,
                "prompt_per_token_ms": prompt_ms / max(prompt_tokens, 1),
                "prompt_per_second": 1000.0 * prompt_tokens / max(prompt_ms, 1),
                "predicted_n": tokens_predicted,
                "predicted_ms": elapsed_ms,
                "predicted_per_token_ms": elapsed_ms / max(tokens_predicted, 1),
                "predicted_per_second": 1000.0 * tokens_predicted / max(elapsed_ms, 1),
            },
        }

        logger.info(f"[LLAMA_CPP] Generation completed, slot: {slot_id}, tokens: {tokens_predicted}, elapsed: {elapsed_ms/1000:.2f}s")

        return response
