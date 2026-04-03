"""Client for interfacing with llama.cpp server API directly, eliminating dependency on llama-cpp-python."""

import requests
import subprocess
import time
import threading
import os
import signal
from pathlib import Path
from typing import Dict, Any, Optional, Generator, Union
from urllib.parse import urljoin
import json


class LlamaCppServer:
    """Manages llama.cpp server process lifecycle."""
    
    def __init__(self, model_path: str, host: str = "localhost", port: int = 8080, **kwargs):
        """Initialize llama.cpp server configuration."""
        self.model_path = model_path
        self.host = host
        self.port = port
        self.process = None
        self.server_url = f"http://{host}:{port}"
        
        # Default llama.cpp server args
        self.default_args = [
            "-m", model_path,
            "-h", host,
            "-p", str(port),
        ]
        
        # Process extra parameters
        self.args = self._process_extra_args(kwargs)
    
    def _process_extra_args(self, kwargs: Dict[str, Any]) -> list:
        """Process additional arguments for llama.cpp server."""
        args = self.default_args[:]
        
        # Map common params to llama.cpp server equivalents
        if 'n_ctx' in kwargs:
            args.extend(["-c", str(kwargs['n_ctx'])])
        if 'n_threads' in kwargs:
            args.extend(["-t", str(kwargs['n_threads'])])
        if 'n_gpu_layers' in kwargs:
            args.extend(["-ngl", str(kwargs['n_gpu_layers'])])
        if 'n_batch' in kwargs:
            args.extend(["-b", str(kwargs['n_batch'])])
        if 'verbose' in kwargs and kwargs['verbose']:
            args.append("-v")
        
        # Additional arguments that might be passed
        for key, value in kwargs.items():
            if key in ['seed', 'n_predict', 'ctx_size'] and value is not None:
                if key == 'seed':
                    args.extend(["--seed", str(value)])
                elif key == 'n_predict':
                    args.extend(["-n", str(value)])
                elif key == 'ctx_size':
                    args.extend(["-c", str(value)])
        
        return args
    
    def start(self) -> bool:
        """Start the llama.cpp server process."""
        try:
            # Find the llama-server executable
            server_executable = self._find_llama_server_executable()
            
            cmd_args = [server_executable] + self.args
            self.process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a bit for the server to start
            time.sleep(2)
            
            # Test that server is responding
            max_retries = 30
            for _ in range(max_retries):
                try:
                    response = requests.get(f"{self.server_url}/health", timeout=5)
                    if response.status_code == 200:
                        print(f"llama.cpp server is ready at {self.server_url}")
                        return True
                except requests.ConnectionError:
                    pass
                time.sleep(1)
            
            # Server didn't respond in time, terminate
            self.stop()
            print(f"llama.cpp server failed to start after {max_retries} attempts")
            return False
            
        except Exception as e:
            print(f"Error starting llama.cpp server: {e}")
            return False
    
    def _find_llama_server_executable(self) -> str:
        """Locate the llama.cpp server executable."""
        # Look for llama-server in standard locations
        possible_paths = [
            # User might have installed llama.cpp separately
            "./llama-server",  # Current directory
            "../llama.cpp/llama-server",  # Parallel llama.cpp checkout
            "../../llama.cpp/llama-server",  # Parent dir with parallel llama.cpp checkout
            "/usr/local/bin/llama-server",  # Standard Linux installation
            "/opt/llama/bin/llama-server",  # Package installation
            "llama-server.exe" if os.name == 'nt' else "llama-server",  # Try PATH
        ]
        
        for path in possible_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        
        # Could not find the executable
        raise RuntimeError(
            "llama.cpp server executable not found. "
            "Please install or compile llama.cpp from https://github.com/ggerganov/llama.cpp"
        )

    def stop(self):
        """Stop the llama.cpp server process."""
        if self.process:
            try:
                # Try graceful shutdown
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                try:
                    self.process.kill()
                except:
                    pass
            finally:
                self.process = None
    
    def is_running(self) -> bool:
        """Check if the server process is still running."""
        return self.process is not None and self.process.poll() is None


class LlamaCppClient:
    """Client to communicate with a running llama.cpp server."""
    
    def __init__(self, server_url: str = "http://localhost:8080"):
        self.server_url = server_url.rstrip('/')
    
    def completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate a completion using the llama.cpp server."""
        url = f"{self.server_url}/completion"
        payload = {
            "prompt": prompt,
            **{k: v for k, v in kwargs.items() if v is not None}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Completion request failed: {e}")
    
    def stream_completion(self, prompt: str, **kwargs) -> Generator[Any, None, None]:
        """Generate streaming completion using the llama.cpp server."""
        url = f"{self.server_url}/completion"
        payload = {
            "prompt": prompt,
            "stream": True,
            **{k: v for k, v in kwargs.items() if v is not None}
        }
        
        try:
            resp = requests.post(url, json=payload, stream=True, timeout=30)
            resp.raise_for_status()
            
            for line in resp.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data_str)
                        yield chunk
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Streaming completion request failed: {e}")

    def tokenize(self, text: str) -> list:
        """Tokenize text using the llama.cpp server."""
        url = f"{self.server_url}/tokenize"
        payload = {"content": text}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json().get('tokens', [])
        except:
            # If tokenize fails, fall back to simple split
            return text.split()

    def detokenize(self, tokens: list) -> str:
        """Convert tokens back to text using the llama.cpp server."""
        url = f"{self.server_url}/detokenize"
        payload = {"tokens": tokens}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json().get('content', '')
        except:
            # If detokenize fails, join tokens with space
            return ' '.join(map(str, tokens))

    def health(self) -> bool:
        """Check server health."""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False