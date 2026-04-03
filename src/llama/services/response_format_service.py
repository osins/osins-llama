"""Response Format Service for handling structured output in chat completions."""

import json
import re
from typing import Any, Dict, Optional
from enum import Enum
from llama.core.logger_manager import logger


class ResponseFormatType(str, Enum):
    """
    Response Format Type 枚举
    表示响应格式的类型，严格遵循 OpenAI API 规范。
    """
    TEXT = "text"
    JSON_OBJECT = "json_object"
    JSON_SCHEMA = "json_schema"


class ResponseFormatService:
    """
    Response Format Service
    处理Chat Completion API中的结构化输出功能。
    严格遵循 OpenAI Structured Outputs 规范。
    """
    
    _instance = None
    
    def __init__(self):
        pass
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @staticmethod
    def get_format_type(response_format: Dict[str, Any]) -> ResponseFormatType:
        """
        获取响应格式类型
        
        Args:
            response_format: 响应格式配置
            
        Returns:
            ResponseFormatType枚举值
        """
        format_type = response_format.get("type", "text")
        try:
            return ResponseFormatType(format_type)
        except ValueError:
            logger.warning(f"Unknown response format type: {format_type}, falling back to text")
            return ResponseFormatType.TEXT
    
    @staticmethod
    def validate_json_response(
        content: str,
        response_format: Dict[str, Any]
    ) -> str:
        """
        验证响应是否符合指定的格式
        
        Args:
            content: 响应内容
            response_format: 响应格式配置
            
        Returns:
            验证后的内容
            
        Raises:
            ValueError: 内容不符合格式要求
        """
        format_type = ResponseFormatService.get_format_type(response_format)
        
        if format_type == ResponseFormatType.TEXT:
            return content
        
        if format_type == ResponseFormatType.JSON_OBJECT:
            try:
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ValueError("Response must be a JSON object, not an array or primitive")
                return content
            except json.JSONDecodeError as e:
                raise ValueError(f"Response is not valid JSON: {e}")
        
        if format_type == ResponseFormatType.JSON_SCHEMA:
            schema = response_format.get("json_schema", {})
            schema_content = schema.get("schema", {})
            
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Response is not valid JSON: {e}")
            
            # 基本schema验证
            errors = ResponseFormatService._validate_against_schema(parsed, schema_content)
            if errors:
                raise ValueError(f"Response does not match schema: {'; '.join(errors)}")
            
            return content
        
        return content
    
    @staticmethod
    def _validate_against_schema(
        data: Any,
        schema: Dict[str, Any],
        path: str = "root"
    ) -> list:
        """
        基本的JSON Schema验证
        
        Args:
            data: 要验证的数据
            schema: JSON Schema
            path: 当前路径（用于错误消息）
            
        Returns:
            错误消息列表
        """
        errors = []
        
        if not schema:
            return errors
        
        schema_type = schema.get("type")
        
        # 类型验证
        if schema_type:
            type_valid = ResponseFormatService._check_type(data, schema_type)
            if not type_valid:
                errors.append(f"Type mismatch at {path}: expected {schema_type}, got {type(data).__name__}")
                return errors
        
        # 对象类型验证
        if schema_type == "object" or (isinstance(data, dict) and "properties" in schema):
            if not isinstance(data, dict):
                errors.append(f"Expected object at {path}")
                return errors
            
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            # 检查必需属性
            for req_prop in required:
                if req_prop not in data:
                    errors.append(f"Missing required property '{req_prop}' at {path}")
            
            # 递归验证属性
            for prop_name, prop_schema in properties.items():
                if prop_name in data:
                    prop_errors = ResponseFormatService._validate_against_schema(
                        data[prop_name],
                        prop_schema,
                        f"{path}.{prop_name}"
                    )
                    errors.extend(prop_errors)
        
        # 数组类型验证
        if schema_type == "array" and "items" in schema:
            if not isinstance(data, list):
                errors.append(f"Expected array at {path}")
                return errors
            
            items_schema = schema.get("items", {})
            for i, item in enumerate(data):
                item_errors = ResponseFormatService._validate_against_schema(
                    item,
                    items_schema,
                    f"{path}[{i}]"
                )
                errors.extend(item_errors)
        
        # 枚举验证
        enum_values = schema.get("enum")
        if enum_values and data not in enum_values:
            errors.append(f"Value at {path} must be one of {enum_values}")
        
        # 最小/最大值验证
        if isinstance(data, (int, float)):
            minimum = schema.get("minimum")
            if minimum is not None and data < minimum:
                errors.append(f"Value at {path} must be >= {minimum}")
            
            maximum = schema.get("maximum")
            if maximum is not None and data > maximum:
                errors.append(f"Value at {path} must be <= {maximum}")
        
        # 字符串长度验证
        if isinstance(data, str):
            min_length = schema.get("minLength")
            if min_length is not None and len(data) < min_length:
                errors.append(f"String at {path} must be at least {min_length} characters")
            
            max_length = schema.get("maxLength")
            if max_length is not None and len(data) > max_length:
                errors.append(f"String at {path} must be at most {max_length} characters")
        
        return errors
    
    @staticmethod
    def _check_type(data: Any, schema_type: str) -> bool:
        """
        检查数据类型是否符合schema类型
        
        Args:
            data: 要检查的数据
            schema_type: schema中定义的类型
            
        Returns:
            是否类型匹配
        """
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "object": dict,
            "array": list,
            "null": type(None)
        }
        
        expected_type = type_mapping.get(schema_type)
        if expected_type is None:
            return True  # 未知类型，跳过验证
        
        if schema_type == "number":
            return isinstance(data, (int, float)) and not isinstance(data, bool)
        
        return isinstance(data, expected_type)
    
    @staticmethod
    def build_json_prompt_suffix(response_format: Dict[str, Any]) -> str:
        """
        构建JSON模式提示后缀
        
        Args:
            response_format: 响应格式配置
            
        Returns:
            提示后缀字符串
        """
        format_type = ResponseFormatService.get_format_type(response_format)
        
        if format_type == ResponseFormatType.JSON_OBJECT:
            return "\n\nRespond with a valid JSON object. Do not include any text outside the JSON object."
        
        if format_type == ResponseFormatType.JSON_SCHEMA:
            schema = response_format.get("json_schema", {})
            schema_definition = schema.get("schema", {})
            schema_str = json.dumps(schema_definition, indent=2)
            return f"\n\nRespond with a JSON object that matches this schema:\n```json\n{schema_str}\n```\n\nDo not include any text outside the JSON object."
        
        return ""
    
    @staticmethod
    def extract_json_from_response(content: str) -> str:
        """
        从响应中提取JSON内容
        
        Args:
            content: 原始响应内容
            
        Returns:
            提取的JSON字符串
        """
        content = content.strip()
        
        # 尝试直接解析
        try:
            json.loads(content)
            return content
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON代码块
        json_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        matches = re.findall(json_block_pattern, content)
        for match in matches:
            try:
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue
        
        # 尝试提取花括号包围的内容
        brace_pattern = r'\{[\s\S]*\}'
        matches = re.findall(brace_pattern, content)
        for match in matches:
            try:
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue
        
        # 返回原始内容
        return content
