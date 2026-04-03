"""
Llama Model Client - 处理 OpenAI API 请求并代理到本地 llama.cpp 服务
提供完整的 OpenAI API 兼容性，包括聊天补全、文本补全等接口
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any, AsyncIterator, Iterator
import requests
import subprocess
import threading
import signal
import os
from pathlib import Path


class LlamaCppProcess:
    """管理 llama.cpp 服务器进程的生命周期"""
    
    def __init__(self, model_path: str, host: str = "127.0.0.1", port: int = 8080, **kwargs):
        self.model_path = model_path
        self.host = host
        self.port = port
        self.server_url = f"http://{host}:{port}"
        self.process = None
        self.stderr_log = None
        self.stdout_log = None
        
        # 验证模型文件存在
        model_path_obj = Path(self.model_path)
        if not model_path_obj.exists():
            raise FileNotFoundError(f"Model file does not exist: {self.model_path}")
        
        # 构建参数
        self.args = self._build_args(kwargs)

    def _build_args(self, extra_args: Dict[str, Any]) -> list:
        """构建启动参数"""
        args = [
            self._get_llama_server_executable(),
            "-m", self.model_path,
            "-h", self.host,
            "-p", str(self.port)
        ]
        
        # 根据额外参数添加命令行选项
        if 'n_ctx' in extra_args:
            args.extend(["-c", str(extra_args['n_ctx'])])
        if 'n_threads' in extra_args:
            args.extend(["-t", str(extra_args['n_threads'])])
        if 'n_gpu_layers' in extra_args:
            args.extend(["-ngl", str(extra_args['n_gpu_layers'])])
        if 'n_batch' in extra_args:
            args.extend(["-b", str(extra_args['n_batch'])])
        if 'verbose' in extra_args:
            args.append("-v")
            
        return args
    
    def _get_llama_server_executable(self) -> str:
        """查找 llama-server 可执行文件"""
        # 查找可执行文件的位置
        import shutil
        possible_locations = [
            # 如果安装了llama.cpp
            shutil.which("llama-server"),
            # Windows路径
            shutil.which("llama-server.exe"),
            # 在可能的安装路径中查找
            "/usr/bin/llama-server",
            "/opt/llama/bin/llama-server",
            "./llama.cpp/llama-server",
        ]
        
        for path in possible_locations:
            if path and Path(path).exists():
                return path
                
        # 如果没有找到，抛出异常
        raise RuntimeError("Cannot find llama-server executable. Install llama.cpp from https://github.com/ggerganov/llama.cpp")

    @property
    def is_running(self) -> bool:
        """检查服务器是否正在运行"""
        return self.process is not None and self.process.poll() is None

    def start(self, timeout: int = 60) -> bool:
        """启动 llama.cpp 服务器"""
        import tempfile
        try:
            # 创建临时日志文件
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='_llama_stdout.log') as stdout_file:
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='_llama_stderr.log') as stderr_file:
                    self.stdout_log = stdout_file.name
                    self.stderr_log = stderr_file.name
            
            with open(self.stdout_log, 'w') as stdout_handle, open(self.stderr_log, 'w') as stderr_handle:
                self.process = subprocess.Popen(
                    self.args,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    stdin=subprocess.DEVNULL
                )
            
            # 等待服务器启动
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(f"{self.server_url}/health", timeout=5)
                    if response.status_code == 200:
                        print(f"Llama server started successfully at {self.server_url}")
                        return True
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
                
            print(f"Timeout: llama server failed to start within {timeout} seconds")
            return False
        except Exception as e:
            print(f"Failed to start llama server: {str(e)}")
            return False

    def stop(self):
        """停止 llama.cpp 服务器"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except Exception as e:
                print(f"Error stopping llama server: {str(e)}")
                
            # 清理日志文件
            try:
                if self.stdout_log and Path(self.stdout_log).exists():
                    Path(self.stdout_log).unlink()
                if self.stderr_log and Path(self.stderr_log).exists():
                    Path(self.stderr_log).unlink()
            except:
                pass


class LlamaModelClient:
    """Llama模型客户端 - 代理OpenAI API请求到本地llama.cpp服务器"""
    
    def __init__(self, model_path: str, host: str = "127.0.0.1", port: Optional[int] = None):
        """
        初始化客户端
        :param model_path: 模型路径
        :param host: 服务器主机地址
        :param port: 服务器端口（如果为None则自动分配）
        """
        if port is None:
            self.port = self._find_free_port()
        else:
            self.port = port
            
        self.model_path = model_path
        self.host = host
        self.server_url = f"http://{host}:{self.port}"
        self._process = LlamaCppProcess(
            model_path=model_path,
            host=host,
            port=self.port
        )
        
    def _find_free_port(self) -> int:
        """查找一个可用的端口"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
        
    def start_server(self) -> bool:
        """启动llama.cpp服务器"""
        return self._process.start()
        
    def stop_server(self):
        """停止llama.cpp服务器"""
        self._process.stop()
        
    @property
    def is_server_running(self) -> bool:
        """检查服务器是否正在运行"""
        return self._process.is_running

    # --- OpenAI API 端点方法 ---
    
    def chat_completions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理 OpenAI /chat/completions 端点请求"""
        url = f"{self.server_url}/v1/chat/completions"
        
        try:
            response = requests.post(url, json=data, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Chat completions API error: {str(e)}")

    def completions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理 OpenAI /completions 端点请求"""
        url = f"{self.server_url}/v1/completions"
        
        try:
            response = requests.post(url, json=data, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Completions API error: {str(e)}")
    
    def embeddings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理 OpenAI /embeddings 端点请求"""
        # llama.cpp目前不直接支持embeddings
        # 返回空的embeddings响应或模拟响应
        input_texts = data.get('input', [])
        if isinstance(input_texts, str):
            input_texts = [input_texts]
        elif not isinstance(input_texts, list):
            input_texts = [str(input_texts)]
            
        # 生成空的嵌入向量占位符 (llama.cpp目前不原生支持embed)
        embeddings = []
        for i, text in enumerate(input_texts):
            # 创建简单的零向量，表明服务不支持embedding
            embedding = {"object": "embedding", "embedding": [0.0] * 384, "index": i}
            embeddings.append(embedding)
            
        return {
            "object": "list", 
            "data": embeddings, 
            "model": Path(self.model_path).name, 
            "usage": {"prompt_tokens": len(input_texts), "total_tokens": len(input_texts)}
        }
    
    def models(self) -> Dict[str, Any]:
        """处理 OpenAI /models 端点请求"""
        return {
            "object": "list",
            "data": [{
                "id": Path(self.model_path).stem,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "llama_cpp"
            }]
        }

    # --- 流式API支持 ---
    
    def stream_chat_completions(self, data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """流式处理聊天补全请求"""
        url = f"{self.server_url}/v1/chat/completions"
        data['stream'] = True
        
        try:
            resp = requests.post(url, json=data, timeout=300, stream=True)
            resp.raise_for_status()
            
            for line in resp.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    chunk_data = line[6:]  # 移除 "data: " 前缀
                    if chunk_data.strip() == "[DONE]":
                        break
                    try:
                        yield json.loads(chunk_data)
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Stream chat completions error: {str(e)}")
    
    def stream_completions(self, data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """流式处理文本补全请求"""
        url = f"{self.server_url}/v1/completions"
        data['stream'] = True
        
        try:
            resp = requests.post(url, json=data, timeout=300, stream=True)
            resp.raise_for_status()
            
            for line in resp.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    chunk_data = line[6:]  # 移除 "data: " 前缀
                    if chunk_data.strip() == "[DONE]":
                        break
                    try:
                        yield json.loads(chunk_data)
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Stream completions error: {str(e)}")