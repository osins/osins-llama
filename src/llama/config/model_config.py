from pydantic import BaseModel


class ModelConfig(BaseModel):
    path: str
    n_ctx: int = 4096
    n_threads: int = 8
    verbose: bool = False