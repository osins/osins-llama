"""Tool Service for handling function calling in chat completions."""

import json
import uuid
from typing import List, Dict, Any, Optional, Callable
from llama.models.chat.tool_call import ToolCall
from llama.models.chat.tool_call_function import FunctionCall
from llama.core.logger_manager import logger


class ToolService:
    """
    Tool Service
    处理Chat Completion API中的工具调用（Function Calling）功能。
    严格遵循 OpenAI Function Calling 规范。
    """
    
    _instance = None
    _tool_handlers: Dict[str, Callable] = {}
    
    def __init__(self):
        self._tool_handlers = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_tool_handler(self, function_name: str, handler: Callable) -> None:
        """
        注册工具处理函数
        
        Args:
            function_name: 函数名称
            handler: 处理函数，接受dict参数，返回dict结果
        """
        self._tool_handlers[function_name] = handler
        logger.info(f"Registered tool handler for function: {function_name}")
    
    def unregister_tool_handler(self, function_name: str) -> None:
        """
        注销工具处理函数
        
        Args:
            function_name: 函数名称
        """
        if function_name in self._tool_handlers:
            del self._tool_handlers[function_name]
            logger.info(f"Unregistered tool handler for function: {function_name}")
    
    def get_tool_handler(self, function_name: str) -> Optional[Callable]:
        """
        获取工具处理函数
        
        Args:
            function_name: 函数名称
            
        Returns:
            处理函数或None
        """
        return self._tool_handlers.get(function_name)
    
    @staticmethod
    def parse_tool_definitions(tools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        解析工具定义为可执行函数映射
        
        Args:
            tools: 工具定义列表
            
        Returns:
            函数名到工具定义的映射
        """
        tool_map = {}
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                name = func.get("name")
                if name:
                    tool_map[name] = {
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {}),
                    }
        return tool_map
    
    @staticmethod
    def build_tool_call(
        function_name: str,
        arguments: Dict[str, Any],
        tool_call_id: Optional[str] = None
    ) -> ToolCall:
        """
        构建工具调用响应
        
        Args:
            function_name: 函数名称
            arguments: 函数参数
            tool_call_id: 工具调用ID（可选）
            
        Returns:
            ToolCall对象
        """
        return ToolCall(
            id=tool_call_id or f"call_{uuid.uuid4().hex[:24]}",
            type="function",
            function=FunctionCall(
                name=function_name,
                arguments=json.dumps(arguments, ensure_ascii=False)
            )
        )
    
    @staticmethod
    def validate_tool_arguments(
        arguments_json: str,
        parameters_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证工具参数
        
        Args:
            arguments_json: JSON格式的参数字符串
            parameters_schema: JSON Schema格式的参数定义
            
        Returns:
            解析后的参数字典
            
        Raises:
            ValueError: 参数格式无效
        """
        try:
            args = json.loads(arguments_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid tool arguments JSON: {e}")
        
        if not isinstance(args, dict):
            raise ValueError("Tool arguments must be a JSON object")
        
        # 基本参数验证（检查必需参数）
        required = parameters_schema.get("required", [])
        properties = parameters_schema.get("properties", {})
        
        for req_param in required:
            if req_param not in args:
                raise ValueError(f"Missing required parameter: {req_param}")
        
        # 检查未知参数（如果不允许额外属性）
        if parameters_schema.get("additionalProperties") is False:
            for key in args:
                if key not in properties:
                    raise ValueError(f"Unknown parameter: {key}")
        
        return args
    
    def execute_tool_call(
        self,
        function_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行工具调用
        
        Args:
            function_name: 函数名称
            arguments: 函数参数
            
        Returns:
            工具执行结果
            
        Raises:
            ValueError: 未找到处理函数
        """
        handler = self.get_tool_handler(function_name)
        if handler is None:
            raise ValueError(f"No handler registered for function: {function_name}")
        
        try:
            result = handler(arguments)
            logger.info(f"Tool call executed: {function_name}")
            return result
        except Exception as e:
            logger.error(f"Tool call failed: {function_name}, error: {e}")
            raise
    
    def process_tool_calls(
        self,
        tool_calls: List[ToolCall],
        tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量处理工具调用
        
        Args:
            tool_calls: 工具调用列表
            tools: 工具定义列表
            
        Returns:
            工具执行结果列表
        """
        tool_map = self.parse_tool_definitions(tools)
        results = []
        
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            func_args_str = tool_call.function.arguments
            
            try:
                # 解析参数
                schema = tool_map.get(func_name, {}).get("parameters", {})
                args = self.validate_tool_arguments(func_args_str, schema)
                
                # 执行工具
                result = self.execute_tool_call(func_name, args)
                
                results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": func_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })
            except Exception as e:
                results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": func_name,
                    "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                })
        
        return results
