from pydantic import BaseModel


class ServiceConfig(BaseModel):
    host: str = "192.168.50.2"
    port: int = 31301
    debug: bool = False
