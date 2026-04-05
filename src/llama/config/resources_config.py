from pydantic import BaseModel


class ResourcesConfig(BaseModel):
    max_prompt_tokens: int = 16384
    max_total_tokens: int = 32768
    max_batch_size: int = 1