# src/llama/models/common/base_model.py

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class BaseDataModel(BaseModel):
    """
    基础数据模型类
    为所有数据模型提供版本控制和其他通用功能
    """
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)  # 禁止额外字段，启用frozen，验证默认值

    schema_version: str = Field(default="1.0.0", description="模型的schema版本")
    
    @classmethod
    def get_schema_version(cls) -> str:
        """
        获取模型的schema版本
        """
        # 获取模型字段的默认值
        field_info = cls.model_fields.get('schema_version')
        if field_info and field_info.default is not None:
            return str(field_info.default)
        return "unknown"