from pydantic import BaseModel


class ResourcesConfig(BaseModel):
    max_prompt_tokens: int = 2048
    max_total_tokens: int = 4096
    max_batch_size: int = 1