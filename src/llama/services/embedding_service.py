"""Embedding Service for generating text embeddings."""

import base64
import struct
from typing import List, Union, Optional
from pathlib import Path
from llama.core.model_manager import ModelManager
from llama.config.config import Config
from llama.models.embeddings.embedding_response import (
    EmbeddingResponse,
    EmbeddingObject,
    EmbeddingUsage
)
from llama.exceptions import ServiceError
from llama.core.logger_manager import logger


class EmbeddingService:
    """
    Embedding Service
    处理文本嵌入向量生成，严格遵循 OpenAI Embeddings API 规范。
    支持llama-cpp-python模型的embed功能。
    """
    
    _instance = None
    
    def __init__(self, config: Config = None):
        self.config = config
        if self.config is None:
            self.config = Config.from_env()
        self.model_manager = ModelManager.get_instance(self.config)
    
    @classmethod
    def get_instance(cls, config: Config = None):
        if cls._instance is None:
            cls._instance = cls(config)
        elif config is not None:
            cls._instance.config = config
        return cls._instance
    
    def _get_model_name(self) -> str:
        """获取模型名称"""
        model_path = self.model_manager.model_path
        if model_path:
            return Path(model_path).name
        return "unknown"
    
    def _count_tokens(self, text: str) -> int:
        """
        简单的token计数（近似值）
        
        Args:
            text: 输入文本
            
        Returns:
            近似token数量
        """
        # 简单估计：平均每4个字符约1个token
        # 这是一个粗略估计，实际应该使用tokenizer
        return max(1, len(text) // 4)
    
    def _encode_embedding_base64(self, embedding: List[float]) -> str:
        """
        将嵌入向量编码为base64格式
        
        Args:
            embedding: 浮点数列表
            
        Returns:
            base64编码字符串
        """
        # 将浮点数列表编码为二进制
        packed = struct.pack(f'<{len(embedding)}f', *embedding)
        return base64.b64encode(packed).decode('ascii')
    
    def _truncate_embedding(self, embedding: List[float], dimensions: int) -> List[float]:
        """
        截断嵌入向量到指定维度
        
        Args:
            embedding: 原始嵌入向量
            dimensions: 目标维度
            
        Returns:
            截断后的嵌入向量
        """
        if dimensions >= len(embedding):
            return embedding
        return embedding[:dimensions]
    
    async def create_embeddings(
        self,
        inputs: Union[str, List[str]],
        model: str,
        encoding_format: str = "float",
        dimensions: Optional[int] = None
    ) -> EmbeddingResponse:
        """
        创建文本嵌入向量
        
        注意：目前llama.cpp服务器没有内置embedding功能
        这个方法需要适应API模式 - 会在未来版本提供更完整的embedding支持
        
        Args:
            inputs: 输入文本或文本列表
            model: 模型名称
            encoding_format: 编码格式 ("float" 或 "base64")
            dimensions: 可选的目标维度
            
        Returns:
            EmbeddingResponse对象
            
        Raises:
            ServiceError: 模型不支持嵌入或生成失败
        """
        # 当前暂不支持embeddings特性因为llama.cpp server API目前没有embedding endpoint
        raise ServiceError(
            "Embedding functionality is not supported when using direct llama.cpp server connection",
            status_code=501
        )
    
    async def create_embeddings_fallback(
        self,
        inputs: Union[str, List[str]],
        model: str,
        encoding_format: str = "float",
        dimensions: Optional[int] = None
    ) -> EmbeddingResponse:
        """
        创建文本嵌入向量的后备方法（使用模型tokenize生成近似embedding）
        当模型不支持embed方法时，尝试使用其他方式生成embedding
        
        Args:
            inputs: 输入文本或文本列表
            model: 模型名称
            encoding_format: 编码格式
            dimensions: 可选的目标维度
            
        Returns:
            EmbeddingResponse对象
        """
        llama_model = self.model_manager.get_model()
        if llama_model is None:
            raise ServiceError("Model not loaded")
        
        # 标准化输入为列表
        if isinstance(inputs, str):
            inputs = [inputs]
        
        embeddings_data = []
        total_tokens = 0
        
        # 尝试获取模型的嵌入维度
        # 大多数LLM模型的隐藏层维度
        embedding_dim = dimensions or 768
        
        for idx, text in enumerate(inputs):
            try:
                # 尝试使用tokenize获取token表示
                if hasattr(llama_model, 'tokenize'):
                    tokens = llama_model.tokenize(text)
                    total_tokens += len(tokens)
                else:
                    total_tokens += self._count_tokens(text)
                    tokens = None
                
                # 生成一个基于文本内容的确定性伪嵌入
                # 注意：这不是真正的语义嵌入，只是占位符
                import hashlib
                import numpy as np
                
                # 使用文本哈希生成确定性随机种子
                text_hash = hashlib.md5(text.encode()).hexdigest()
                seed = int(text_hash[:8], 16)
                rng = np.random.RandomState(seed)
                
                # 生成伪嵌入向量
                embedding = rng.randn(embedding_dim).astype(np.float32).tolist()
                
                # 归一化
                norm = sum(x**2 for x in embedding) ** 0.5
                embedding = [x / norm for x in embedding]
                
                if encoding_format == "base64":
                    embedding_output = self._encode_embedding_base64(embedding)
                else:
                    embedding_output = embedding
                
                embeddings_data.append(EmbeddingObject(
                    object="embedding",
                    embedding=embedding_output,
                    index=idx
                ))
                
                logger.warning(
                    f"Using fallback embedding generation for input {idx}. "
                    "This is NOT a real semantic embedding."
                )
                
            except Exception as e:
                logger.error(f"Fallback embedding generation failed for input {idx}: {e}", exc_info=True)
                raise ServiceError(f"Embedding generation failed: {str(e)}")
        
        response = EmbeddingResponse(
            object="list",
            data=embeddings_data,
            model=self._get_model_name(),
            usage=EmbeddingUsage(
                prompt_tokens=total_tokens,
                total_tokens=total_tokens
            )
        )
        
        return response
