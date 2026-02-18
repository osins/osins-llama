from pydantic import BaseModel


class ModelConfig(BaseModel):
    path: str
    n_ctx: int = 4096
    n_threads: int = 8
    n_gpu_layers: int = -1
    n_batch: int = 512
    verbose: bool = False