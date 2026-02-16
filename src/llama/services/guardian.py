"""守护进程模块，用于监控和管理osins-llama服务进程"""
import os
import sys
import time
import signal
import json
import subprocess
import threading
import queue
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import yaml

from ..cli.process import ProcessManager
from ..cli.pid_file_manager import PidFileManager
from ..models.pid_data import PidData
from ..utils.pid_tools import is_process_running
from src.llama.core.logger_manager import logger


class GuardianConfig:
    """守护进程配置类"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or './guardian_config.yaml'
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            'max_restarts': 5,
            'restart_interval': 5,  # 重启间隔（秒）
            'check_interval': 5,    # 检查间隔（秒）
            'exponential_backoff_factor': 2,
            'max_backoff_time': 300,  # 最大退避时间（秒）
            'log_level': 'INFO',
            'log_file': './logs/guardian.log',
            'log_max_bytes': 10485760,  # 10MB
            'log_backup_count': 5,
            'gpu_monitoring': True,
            'gpu_check_interval': 30,  # GPU检查间隔（秒）
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        default_config.update(loaded_config)
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
        
        # 更新实例属性
        for key, value in default_config.items():
            setattr(self, key, value)


class LogCapture:
    """日志捕获类"""
    
    def __init__(self, log_queue: queue.Queue, logger: logging.Logger):
        self.log_queue = log_queue
        self.logger = logger
        
    def write(self, message: str):
        if message.strip():  # 忽略空白行
            self.log_queue.put(message.strip())
            
    def flush(self):
        pass  # 确保兼容性


class GuardianService:
    """守护进程服务类"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = GuardianConfig(config_path)
        # 使用全局logger实例，不再使用setup_logger
        self.logger = logger
        self.running = False
        self.process_manager = ProcessManager(expected_cmd_keyword="llama.api.server")
        self.pid_manager = PidFileManager()
        self.restart_count = 0
        self.last_restart_time = 0
        self.gpu_monitoring_thread = None
        self.gpu_monitoring_running = False
        
        # 设置信号处理器
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # GPU 监控相关
        self.gpu_monitoring_enabled = self.config.gpu_monitoring
        if self.gpu_monitoring_enabled:
            try:
                import torch  # 尝试导入PyTorch以检查GPU支持
                self.torch_available = True
                self.logger.info("PyTorch available, GPU monitoring enabled")
            except ImportError:
                self.torch_available = False
                self.logger.warning("PyTorch not available, GPU monitoring disabled")
        else:
            self.torch_available = False
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"Received signal {signum}, shutting down guardian service...")
        self.stop()
    
    def start_gpu_monitoring(self):
        """启动GPU监控线程"""
        if not self.gpu_monitoring_enabled or not self.torch_available:
            return
            
        self.gpu_monitoring_running = True
        self.gpu_monitoring_thread = threading.Thread(target=self._gpu_monitor_loop, daemon=True)
        self.gpu_monitoring_thread.start()
        self.logger.info("GPU monitoring thread started")
    
    def stop_gpu_monitoring(self):
        """停止GPU监控线程"""
        if self.gpu_monitoring_thread:
            self.gpu_monitoring_running = False
            if self.gpu_monitoring_thread.is_alive():
                self.gpu_monitoring_thread.join(timeout=2.0)
            self.logger.info("GPU monitoring thread stopped")
    
    def _gpu_monitor_loop(self):
        """GPU监控循环"""
        import torch
        
        while self.gpu_monitoring_running:
            try:
                if torch.cuda.is_available():
                    gpu_count = torch.cuda.device_count()
                    for i in range(gpu_count):
                        gpu_name = torch.cuda.get_device_name(i)
                        memory_info = torch.cuda.memory_allocated(i), torch.cuda.memory_reserved(i)
                        
                        self.logger.debug(
                            f"GPU {i} ({gpu_name}): "
                            f"Allocated={memory_info[0]/1024**2:.1f}MB, "
                            f"Reserved={memory_info[1]/1024**2:.1f}MB"
                        )
                        
                        # 检查GPU内存占用是否异常高（超过90%）
                        total_memory = torch.cuda.get_device_properties(i).total_memory
                        allocated_memory = torch.cuda.memory_allocated(i)
                        if allocated_memory > total_memory * 0.9:
                            self.logger.warning(
                                f"GPU {i} memory usage is high: "
                                f"{allocated_memory/total_memory*100:.1f}%"
                            )
                
                time.sleep(self.config.gpu_check_interval)
            except Exception as e:
                self.logger.error(f"Error in GPU monitoring: {e}")
                time.sleep(self.config.gpu_check_interval)
    
    def exponential_backoff_delay(self) -> float:
        """计算指数退避延迟"""
        elapsed_since_last_restart = time.time() - self.last_restart_time
        if elapsed_since_last_restart > 300:  # 5分钟重置计数
            self.restart_count = 0
            
        delay = min(
            self.config.restart_interval * (self.config.exponential_backoff_factor ** self.restart_count),
            self.config.max_backoff_time
        )
        return delay
    
    def start_service(self):
        """启动守护服务"""
        if self.running:
            self.logger.warning("Guardian service is already running")
            return
            
        self.logger.info("Starting guardian service...")
        self.running = True
        
        # 启动GPU监控
        self.start_gpu_monitoring()
        
        # 主监控循环
        while self.running:
            try:
                # 检查主服务是否运行
                if not self.process_manager.is_running():
                    self.logger.warning("Main service is not running, attempting restart...")
                    
                    # 计算重启延迟
                    delay = self.exponential_backoff_delay()
                    self.logger.info(f"Waiting {delay}s before restart (exponential backoff)...")
                    time.sleep(delay)
                    
                    # 执行重启
                    self._perform_restart()
                else:
                    # 服务正常运行，重置重启计数
                    self.restart_count = 0
                    
                # 等待下次检查
                time.sleep(self.config.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("KeyboardInterrupt received, stopping guardian service...")
                break
            except Exception as e:
                self.logger.error(f"Error in guardian loop: {e}")
                time.sleep(self.config.check_interval)
        
        self.logger.info("Guardian service stopped")
    
    def _perform_restart(self):
        """执行重启操作"""
        try:
            # 获取PID数据用于重启
            pid_data = self.pid_manager.read(validate=True)
            if not pid_data:
                self.logger.error("No PID data found, cannot restart service")
                return
                
            self.logger.info(f"Restarting service (attempt #{self.restart_count + 1})")
            
            # 停止当前进程
            self.process_manager.stop()
            
            # 等待一段时间确保进程完全停止
            time.sleep(2)
            
            # 启动新进程
            self.process_manager.start(pid_data)

            # 更新重启统计
            self.restart_count += 1
            self.last_restart_time = time.time()

            self.logger.info(f"Service restarted successfully on {pid_data.host}:{pid_data.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to restart service: {e}")
    
    def stop(self):
        """停止守护服务"""
        self.logger.info("Stopping guardian service...")
        self.running = False
        self.stop_gpu_monitoring()
    
    def get_status(self) -> Dict:
        """获取守护服务状态"""
        main_service_running = self.process_manager.is_running()
        main_service_pid = self.process_manager.get_pid() if main_service_running else None
        
        return {
            'guardian_running': self.running,
            'main_service_running': main_service_running,
            'main_service_pid': main_service_pid,
            'restart_count': self.restart_count,
            'last_restart_time': self.last_restart_time,
            'gpu_monitoring_enabled': self.gpu_monitoring_enabled,
            'config': {
                'max_restarts': self.config.max_restarts,
                'check_interval': self.config.check_interval,
                'restart_interval': self.config.restart_interval,
            }
        }


def main():
    """守护进程入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Llama Service Guardian')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--action', type=str, choices=['start', 'stop', 'status'], 
                       default='start', help='Action to perform')
    
    args = parser.parse_args()
    
    guardian = GuardianService(config_path=args.config)
    
    if args.action == 'start':
        guardian.start_service()
    elif args.action == 'stop':
        guardian.stop()
    elif args.action == 'status':
        status = guardian.get_status()
        print(json.dumps(status, indent=2, default=str))


if __name__ == "__main__":
    main()