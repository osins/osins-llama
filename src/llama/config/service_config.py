from pydantic import BaseModel


class ServiceConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 31301
    debug: bool = False