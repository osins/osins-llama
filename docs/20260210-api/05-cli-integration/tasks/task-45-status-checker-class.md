# StatusChecker类实现

## 概述

StatusChecker类负责检查服务器和进程的运行状态，提供健康状况信息。

## 实现要求

1. 实现服务器健康检查功能
2. 实现进程状态检查功能
3. 提供综合状态检查
4. 处理各种异常情况
5. 记录响应时间

## 代码实现

```python
import requests
from typing import Dict, Any, Optional
import psutil
from pathlib import Path
import logging


class StatusChecker:
    """状态检查器"""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def check_server_health(self, api_url: str, timeout: int = 10) -> Dict[str, Any]:
        """检查服务器健康状态"""
        self.logger.debug(f"Checking server health at {api_url}")

        try:
            response = requests.get(f"{api_url}/health", timeout=timeout)

            if response.status_code == 200:
                try:
                    health_data = response.json()
                    result = {
                        'status': 'healthy',
                        'details': health_data,
                        'response_time': response.elapsed.total_seconds()
                    }
                    self.logger.info(f"Server health check succeeded: {result}")
                    return result
                except ValueError:
                    # 响应不是JSON格式
                    result = {
                        'status': 'healthy',
                        'details': {'message': response.text[:100]},
                        'response_time': response.elapsed.total_seconds()
                    }
                    self.logger.info(f"Server health check succeeded (non-JSON response): {result}")
                    return result
            else:
                result = {
                    'status': 'unhealthy',
                    'details': {'status_code': response.status_code},
                    'response_time': response.elapsed.total_seconds()
                }
                self.logger.warning(f"Server health check failed: {result}")
                return result
        except requests.Timeout:
            result = {
                'status': 'timeout',
                'details': {'error': f'Request timed out after {timeout} seconds'},
                'response_time': timeout
            }
            self.logger.error(f"Server health check timed out: {result}")
            return result
        except requests.ConnectionError as e:
            result = {
                'status': 'error',
                'details': {'error': f'Connection error: {str(e)}'},
                'response_time': 0
            }
            self.logger.error(f"Server health check connection error: {result}")
            return result
        except requests.RequestException as e:
            result = {
                'status': 'error',
                'details': {'error': f'Request error: {str(e)}'},
                'response_time': 0
            }
            self.logger.error(f"Server health check request error: {result}")
            return result
        except Exception as e:
            result = {
                'status': 'error',
                'details': {'error': f'Unexpected error: {str(e)}'},
                'response_time': 0
            }
            self.logger.error(f"Server health check unexpected error: {result}")
            return result

    def check_process_status(self, pid_file: Path) -> Dict[str, Any]:
        """检查进程状态"""
        self.logger.debug(f"Checking process status for PID file: {pid_file}")

        if not pid_file.exists():
            result = {
                'running': False,
                'error': 'PID file does not exist'
            }
            self.logger.warning(f"PID file does not exist: {pid_file}")
            return result

        try:
            pid_content = pid_file.read_text().strip()
            pid = int(pid_content)

            process = psutil.Process(pid)
            is_running = process.is_running()

            # 获取CPU和内存使用率，第一次调用可能不准确，所以先调用一次
            process.cpu_percent(interval=None)  # 初始化CPU测量

            result = {
                'running': is_running,
                'pid': pid,
                'process_info': {
                    'name': process.name(),
                    'status': process.status(),
                    'cpu_percent': process.cpu_percent(interval=0.1),  # 获取可靠值
                    'memory_percent': process.memory_percent()
                } if is_running else None
            }

            if is_running:
                self.logger.info(f"Process is running: {result}")
            else:
                self.logger.info(f"Process is not running: {result}")

            return result
        except ValueError:
            result = {
                'running': False,
                'error': 'Invalid PID in file'
            }
            self.logger.error(f"Invalid PID in file: {pid_file}")
            return result
        except psutil.NoSuchProcess:
            result = {
                'running': False,
                'error': 'Process not found'
            }
            self.logger.warning(f"Process not found: {pid_file}")
            return result
        except psutil.AccessDenied:
            result = {
                'running': False,
                'error': 'Access denied to process'
            }
            self.logger.error(f"Access denied to process: {pid_file}")
            return result
        except Exception as e:
            result = {
                'running': False,
                'error': str(e)
            }
            self.logger.error(f"Error checking process status: {result}")
            return result

    def combined_status_check(self, pid_file: Path, api_url: str) -> Dict[str, Any]:
        """综合状态检查"""
        self.logger.info(f"Performing combined status check for PID file: {pid_file}, API URL: {api_url}")

        process_status = self.check_process_status(pid_file)
        api_status = None

        if process_status['running']:
            api_status = self.check_server_health(api_url)

        overall_status = 'healthy' if process_status['running'] and (api_status and api_status['status'] == 'healthy') else 'unhealthy'

        result = {
            'process': process_status,
            'api': api_status,
            'overall_status': overall_status
        }

        self.logger.info(f"Combined status check result: {result}")
        return result
```

## 验证标准

- [ ] 服务器健康检查功能实现完整
- [ ] 进程状态检查功能
- [ ] 综合状态检查支持
- [ ] 异常情况处理
- [ ] 响应时间记录
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 验证API URL安全性
- 防止健康检查被滥用
- 验证PID文件安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12