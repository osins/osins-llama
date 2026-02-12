"""
模型Schema版本跟踪器
用于跟踪和管理数据模型的版本变化
"""
from typing import Dict, Type, Any
from pydantic import BaseModel
from hashlib import sha256
import json


class SchemaVersionTracker:
    """
    Schema版本跟踪器
    用于计算和跟踪模型的schema哈希值，确保版本一致性
    """
    
    @staticmethod
    def compute_schema_hash(model_class: Type[BaseModel]) -> str:
        """
        计算模型schema的哈希值
        """
        # 获取模型的JSON schema
        schema = model_class.model_json_schema()
        
        # 将schema转换为标准化的JSON字符串
        schema_str = json.dumps(schema, sort_keys=True, separators=(',', ':'))
        
        # 计算SHA256哈希
        hash_obj = sha256(schema_str.encode('utf-8'))
        return hash_obj.hexdigest()
    
    @staticmethod
    def get_model_version_info(model_class: Type[BaseModel]) -> Dict[str, Any]:
        """
        获取模型的版本信息
        """
        schema_hash = SchemaVersionTracker.compute_schema_hash(model_class)
        
        # 尝试获取版本号
        version = "unknown"
        if hasattr(model_class, 'get_schema_version'):
            version = model_class.get_schema_version()
        elif hasattr(model_class, 'schema_version'):
            # 如果schema_version是字段默认值
            field_info = model_class.model_fields.get('schema_version')
            if field_info and field_info.default:
                version = field_info.default
        
        return {
            "model_name": model_class.__name__,
            "schema_hash": schema_hash,
            "version": version,
            "module": model_class.__module__
        }


# 预计算常用模型的schema哈希
MODEL_SCHEMA_HASHES: Dict[str, str] = {}


def register_model_for_version_tracking(model_class: Type[BaseModel]) -> Type[BaseModel]:
    """
    注册模型以进行版本跟踪
    """
    global MODEL_SCHEMA_HASHES
    schema_hash = SchemaVersionTracker.compute_schema_hash(model_class)
    MODEL_SCHEMA_HASHES[model_class.__name__] = schema_hash
    return model_class


# 便捷函数，用于装饰器方式注册模型
track_schema_version = register_model_for_version_tracking