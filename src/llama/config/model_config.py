from typing import Optional
from pydantic import BaseModel, field_validator


class ModelConfig(BaseModel):
    path: Optional[str] = ""  # 使模型路径可选
    n_ctx: int = 8192
    n_threads: int = 10
    n_gpu_layers: int = 16
    n_batch: int = 1024
    verbose: bool = True
    device: Optional[str] = "cuda0"
    kv_offload: bool = True
    flash_attn: Optional[str] = "auto"
    repack: bool = True
    chat_template: Optional[str] = None

    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        # 如果提供但不能为空字符串，但如果是空字符串则表示不指定模型
        if v and v.strip() == "":
            v = None
        return v or ""
