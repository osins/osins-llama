"""llama.cpp compatible completion response models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class GenerationSettings(BaseModel):
    """Generation settings returned in llama.cpp response."""
    seed: int = -1
    temperature: float = 0.8
    dynatemp_range: float = 0.0
    dynatemp_exponent: float = 1.0
    top_k: int = 40
    top_p: float = 0.95
    min_p: float = 0.05
    top_n_sigma: float = -1.0
    xtc_probability: float = 0.0
    xtc_threshold: float = 0.1
    typical_p: float = 1.0
    repeat_last_n: int = 64
    repeat_penalty: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    dry_multiplier: float = 0.0
    dry_base: float = 1.75
    dry_allowed_length: int = 2
    dry_penalty_last_n: int = -1
    dry_sequence_breakers: List[str] = Field(default_factory=lambda: ["\n", ":", "\"", "*"])
    mirostat: int = 0
    mirostat_tau: float = 5.0
    mirostat_eta: float = 0.1
    stop: List[str] = Field(default_factory=list)
    max_tokens: int = -1
    n_predict: int = -1
    n_keep: int = 0
    n_discard: int = 0
    ignore_eos: bool = False
    stream: bool = False
    logit_bias: List[Any] = Field(default_factory=list)
    n_probs: int = 0
    min_keep: int = 0
    grammar: str = ""
    grammar_lazy: bool = False
    grammar_triggers: List[Any] = Field(default_factory=list)
    preserved_tokens: List[Any] = Field(default_factory=list)
    chat_format: str = "Content-only"
    reasoning_format: str = "deepseek"
    reasoning_in_content: bool = False
    thinking_forced_open: bool = False
    samplers: List[str] = Field(default_factory=lambda: [
        "penalties", "dry", "top_n_sigma", "top_k", "typ_p", "top_p", "min_p", "xtc", "temperature"
    ])
    speculative_n_max: int = Field(default=16, alias="speculative.n_max")
    speculative_n_min: int = Field(default=0, alias="speculative.n_min")
    speculative_p_min: float = Field(default=0.75, alias="speculative.p_min")
    speculative_type: str = Field(default="none", alias="speculative.type")
    timings_per_token: bool = False
    post_sampling_probs: bool = False
    backend_sampling: bool = False
    lora: List[Any] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class Timings(BaseModel):
    """Timings information returned in llama.cpp response."""
    cache_n: int = 0
    prompt_n: int = 0
    prompt_ms: float = 0.0
    prompt_per_token_ms: float = 0.0
    prompt_per_second: float = 0.0
    predicted_n: int = 0
    predicted_ms: float = 0.0
    predicted_per_token_ms: float = 0.0
    predicted_per_second: float = 0.0


class LlamaCompletionChunk(BaseModel):
    """llama.cpp compatible streaming chunk response."""
    index: int = 0
    content: str = ""
    tokens: List[int] = Field(default_factory=list)
    id_slot: int = -1
    stop: bool = False
    model: str = ""
    tokens_predicted: int = 0
    tokens_evaluated: int = 0
    generation_settings: Optional[GenerationSettings] = None
    prompt: str = ""
    has_new_line: bool = False
    truncated: bool = False
    stop_type: str = ""
    stopping_word: str = ""
    tokens_cached: int = 0
    timings: Optional[Timings] = None


class LlamaCompletionResponse(BaseModel):
    """llama.cpp compatible non-streaming response."""
    index: int = 0
    content: str = ""
    tokens: List[int] = Field(default_factory=list)
    id_slot: int = -1
    stop: bool = True
    model: str = ""
    tokens_predicted: int = 0
    tokens_evaluated: int = 0
    generation_settings: Optional[GenerationSettings] = None
    prompt: str = ""
    has_new_line: bool = False
    truncated: bool = False
    stop_type: str = "limit"
    stopping_word: str = ""
    tokens_cached: int = 0
    timings: Optional[Timings] = None
