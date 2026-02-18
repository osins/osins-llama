from typing import Optional
from pydantic import BaseModel


class ModelConfig(BaseModel):
    path: str
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
