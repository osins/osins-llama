from dataclasses import dataclass
from typing import Optional

@dataclass
class PidData:
    """PID file data model"""
    pid: int
    model_path: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    n_ctx: Optional[int] = None
    n_threads: Optional[int] = None
    api_keys: Optional[str] = None
    max_concurrent_requests: Optional[int] = None
    rate_limit_requests: Optional[int] = None
    rate_limit_window: Optional[int] = None
    debug: Optional[bool] = None
    format_version: int = 1