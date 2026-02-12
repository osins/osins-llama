# src/llama/models/__init__.py

"""
数据模型包
包含所有API所需的数据模型，严格遵循OpenAI API规范
"""

# 显式导入子包以使mypy能够识别
from . import common
from . import chat
from . import legacy

from .common import *
from .chat import *
from .legacy import *
from .version_tracker import SchemaVersionTracker, track_schema_version

__all__ = tuple(
    list(common.__all__) +
    list(chat.__all__) +
    list(legacy.__all__) +
    ["SchemaVersionTracker", "track_schema_version"]
)