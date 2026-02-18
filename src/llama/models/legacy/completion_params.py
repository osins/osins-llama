# src/llama/models/legacy/completion_params.py

from pydantic import ConfigDict, Field
from typing import Optional, Union, List, Dict, Any
from typing import Literal
from ..common.base_model import BaseDataModel
from pydantic import field_validator
from typing import cast


class CompletionParams(BaseDataModel):
    """
    Completion Params 数据模型
    表示 Legacy Completion API 的通用生成参数，严格遵循 OpenAI Completions API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    model: Optional[str] = Field(default="", min_length=0, max_length=255)
    prompt: Union[str, List[str]] = Field(..., max_length=100000)
    max_tokens: Optional[Union[int, str]] = Field(default=16, description="限制最大token数")
    max_new_tokens: Optional[Union[int, str]] = Field(default=16, description="限制最大新token数")
    temperature: Optional[Union[float, str]] = Field(default=1.0, description="温度参数")
    top_p: Optional[Union[float, str]] = Field(default=1.0, description="top_p 参数")
    typical_p: Optional[Union[float, str]] = Field(default=1.0, description="typical_p 参数")
    typical: Optional[Union[float, str]] = Field(default=1.0, description="typical 参数")
    min_p: Optional[Union[float, str]] = Field(default=0.0, description="min_p 参数")
    repetition_penalty: Optional[Union[float, str]] = Field(default=1.0, description="重复惩罚参数")
    frequency_penalty: Optional[Union[float, str]] = Field(default=0.0, description="频率惩罚参数")
    presence_penalty: Optional[Union[float, str]] = Field(default=0.0, description="存在惩罚参数")
    top_k: Optional[Union[int, str]] = Field(default=0, description="top_k 参数")
    skew: Optional[Union[float, str]] = Field(default=0.0, description="skew 参数")
    min_tokens: Optional[Union[int, str]] = Field(default=0, description="最小token数")
    add_bos_token: Optional[Union[bool, str]] = Field(default=True, description="是否添加bos token")
    smoothing_factor: Optional[Union[float, str]] = Field(default=0.0, description="平滑因子")
    smoothing_curve: Optional[Union[float, str]] = Field(default=1.0, description="平滑曲线")
    dry_allowed_length: Optional[Union[int, str]] = Field(default=2, description="dry allowed length")
    dry_multiplier: Optional[Union[float, str]] = Field(default=0.0, description="dry multiplier")
    dry_base: Optional[Union[float, str]] = Field(default=1.75, description="dry base")
    dry_sequence_breakers: Optional[List[str]] = Field(default=["\n", ":", "\"", "*"], description="dry sequence breakers")
    dry_penalty_last_n: Optional[Union[int, str]] = Field(default=0, description="dry penalty last n")
    max_tokens_second: Optional[Union[float, str]] = Field(default=0.0, description="max tokens per second")
    samplers: Optional[List[str]] = Field(default=["top_k", "top_p", "top_a", "typical", "temperature"], description="采样器列表")
    stopping_strings: Optional[List[str]] = Field(default=[], description="停止字符串列表")
    stop: Optional[Union[str, List[str]]] = Field(default=None, max_length=10, description="停止词")
    truncation_length: Optional[Union[int, str]] = Field(default=0, description="截断长度")
    ban_eos_token: Optional[Union[bool, str]] = Field(default=False, description="是否禁止eos token")
    skip_special_tokens: Optional[Union[bool, str]] = Field(default=True, description="是否跳过特殊token")
    include_reasoning: Optional[Union[bool, str]] = Field(default=False, description="是否包含推理")
    top_a: Optional[Union[float, str]] = Field(default=0.0, description="top_a 参数")
    tfs: Optional[Union[float, str]] = Field(default=1.0, description="tfs 参数")
    mirostat_mode: Optional[Union[int, str]] = Field(default=0, description="mirostat模式")
    mirostat_tau: Optional[Union[float, str]] = Field(default=5.0, description="mirostat tau")
    mirostat_eta: Optional[Union[float, str]] = Field(default=0.1, description="mirostat eta")
    custom_token_bans: Optional[str] = Field(default="", description="自定义token禁用")
    banned_strings: Optional[List[str]] = Field(default=[], description="禁用字符串列表")
    api_type: Optional[str] = Field(default="openai", description="API类型")
    api_server: Optional[str] = Field(default="", description="API服务器")
    xtc_threshold: Optional[Union[float, str]] = Field(default=0.1, description="xtc阈值")
    xtc_probability: Optional[Union[float, str]] = Field(default=0.0, description="xtc概率")
    nsigma: Optional[Union[float, str]] = Field(default=0.0, description="nsigma参数")
    top_n_sigma: Optional[Union[int, str]] = Field(default=0, description="top n sigma")
    min_keep: Optional[Union[int, str]] = Field(default=0, description="最小保持数")
    n: Optional[Union[int, str]] = Field(default=1, description="生成数量")
    rep_pen: Optional[Union[float, str]] = Field(default=1.0, description="重复惩罚")
    rep_pen_range: Optional[Union[int, str]] = Field(default=0, description="重复惩罚范围")
    repetition_penalty_range: Optional[Union[int, str]] = Field(default=0, description="重复惩罚范围")
    guidance_scale: Optional[Union[float, str]] = Field(default=1.0, description="引导缩放")
    negative_prompt: Optional[str] = Field(default="", description="负向提示")
    repeat_penalty: Optional[Union[float, str]] = Field(default=1.0, description="重复惩罚")
    repeat_last_n: Optional[Union[int, str]] = Field(default=0, description="重复最后N个")
    n_predict: Optional[Union[int, str]] = Field(default=-1, description="预测数量")
    num_predict: Optional[Union[int, str]] = Field(default=-1, description="预测数量")
    num_ctx: Optional[Union[int, str]] = Field(default=2048, description="上下文数量")
    mirostat: Optional[Union[int, str]] = Field(default=0, description="mirostat")
    ignore_eos: Optional[Union[bool, str]] = Field(default=False, description="忽略EOS")
    rep_pen_slope: Optional[Union[float, str]] = Field(default=0.0, description="重复惩罚斜率")
    logit_bias: Optional[Union[Dict[str, Any], List[Any]]] = Field(default=None, description="logit偏差")
    grammar: Optional[str] = Field(default="", description="语法")
    cache_prompt: Optional[Union[bool, str]] = Field(default=False, description="缓存提示")
    stream: Optional[Union[bool, str]] = Field(default=False, description="流式传输")
    user: Optional[str] = Field(default=None, min_length=1, max_length=255, description="用户")
    best_of: Optional[Union[int, str]] = Field(default=1, description="best_of参数")
    
    @field_validator('max_tokens', 'max_new_tokens', 'top_k', 'min_tokens', 'dry_allowed_length', 'dry_penalty_last_n', 
                     'truncation_length', 'top_n_sigma', 'min_keep', 'n', 'rep_pen_range', 'repetition_penalty_range', 
                     'repeat_last_n', 'n_predict', 'num_predict', 'num_ctx', 'mirostat_mode', 'mirostat',
                     mode='before')
    @classmethod
    def validate_int_field(cls, v):
        if v is None:
            return v
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"Cannot convert {v} to integer")
        return v
    
    @field_validator('temperature', 'top_p', 'typical_p', 'typical', 'min_p', 'repetition_penalty', 
                     'frequency_penalty', 'presence_penalty', 'skew', 'smoothing_factor', 'smoothing_curve',
                     'dry_multiplier', 'dry_base', 'max_tokens_second', 'xtc_threshold', 'xtc_probability',
                     'nsigma', 'top_a', 'tfs', 'mirostat_tau', 'mirostat_eta', 'rep_pen', 'guidance_scale',
                     'repeat_penalty', 'rep_pen_slope', mode='before')
    @classmethod
    def validate_float_field(cls, v):
        if v is None:
            return v
        if isinstance(v, float):
            return v
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Cannot convert {v} to float")
        return v
    
    @field_validator('logit_bias', mode='before')
    @classmethod
    def validate_logit_bias(cls, v):
        if v is None:
            return v
        if isinstance(v, dict):
            return v
        if isinstance(v, list):
            # 如果是空列表，转换为空字典
            if len(v) == 0:
                return {}
            # 如果是非空列表，抛出错误或转换为字典
            # 对于OpenAI兼容性，我们将其转换为空字典
            return {}
        return v

    @field_validator('add_bos_token', 'ban_eos_token', 'skip_special_tokens', 'include_reasoning',
                     'cache_prompt', 'stream', 'ignore_eos', mode='before')
    @classmethod
    def validate_bool_field(cls, v):
        if v is None:
            return v
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            if v.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif v.lower() in ('false', '0', 'no', 'off'):
                return False
            else:
                raise ValueError(f"Cannot convert {v} to boolean")
        return v