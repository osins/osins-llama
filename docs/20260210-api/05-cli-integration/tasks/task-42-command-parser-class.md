# CommandParser类实现

## 概述

CommandParser类负责解析CLI命令的参数，将用户输入转换为内部数据结构。

## 实现要求

1. 实现命令参数解析功能
2. 支持多种命令的参数解析
3. 提供类型校验和安全处理
4. 验证路径安全性
5. 处理API密钥格式

## 代码实现

```python
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import re


class CommandParser:
    """命令解析器"""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def parse_start_command(self, args: Dict[str, Any]) -> StartParams:
        """解析启动命令参数"""
        try:
            # 类型校验和转换
            port = self._convert_to_int(args.get('port', 31301), 'port', 1024, 65535)
            n_ctx = self._convert_to_int(args.get('n_ctx', 2048), 'n_ctx', 1, 32768)
            n_threads = self._convert_to_int(args.get('n_threads', 8), 'n_threads', 1, 128)
            max_concurrent_requests = self._convert_to_int(args.get('max_concurrent_requests', 10), 'max_concurrent_requests', 1, 1000)
            rate_limit_requests = self._convert_to_int(args.get('rate_limit_requests', 60), 'rate_limit_requests', 0, 10000)
            rate_limit_window = self._convert_to_int(args.get('rate_limit_window', 60), 'rate_limit_window', 1, 3600)
            debug = self._convert_to_bool(args.get('debug', False))

            # 路径安全处理
            pid_file = self._validate_path(args.get('pid_file', './llama.pid'), create_parents=True)

            # API密钥处理
            api_keys = self._parse_api_keys(args.get('api_keys'))

            # 构造参数对象
            return StartParams(
                model_path=self._validate_path(args.get('model_path'), must_exist=True),
                host=args.get('host', '0.0.0.0'),
                port=port,
                n_ctx=n_ctx,
                n_threads=n_threads,
                api_keys=api_keys,
                max_concurrent_requests=max_concurrent_requests,
                rate_limit_requests=rate_limit_requests,
                rate_limit_window=rate_limit_window,
                debug=debug,
                pid_file=pid_file
            )
        except ValueError as e:
            self.logger.error(f"Invalid parameter in start command: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error parsing start command: {str(e)}")
            raise

    def parse_stop_command(self, args: Dict[str, Any]) -> StopParams:
        """解析停止命令参数"""
        try:
            # 路径安全处理
            pid_file = self._validate_path(args.get('pid_file', './llama.pid'), create_parents=True)

            force = self._convert_to_bool(args.get('force', False))

            return StopParams(
                pid_file=pid_file,
                force=force
            )
        except Exception as e:
            self.logger.error(f"Error parsing stop command: {str(e)}")
            raise

    def parse_status_command(self, args: Dict[str, Any]) -> StatusParams:
        """解析状态命令参数"""
        try:
            # 路径安全处理
            pid_file = self._validate_path(args.get('pid_file', './llama.pid'), create_parents=True)

            api_url = args.get('api_url', 'http://localhost:31301')

            return StatusParams(
                pid_file=pid_file,
                api_url=api_url
            )
        except Exception as e:
            self.logger.error(f"Error parsing status command: {str(e)}")
            raise

    def parse_config_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置命令参数"""
        try:
            action = args.get('action', 'show')
            if action not in ['show', 'set', 'reset']:
                raise ValueError(f"Invalid config action: {action}. Valid actions: show, set, reset")

            return {
                'action': action,
                'key': args.get('key'),
                'value': args.get('value'),
                'config_file': args.get('config_file')
            }
        except Exception as e:
            self.logger.error(f"Error parsing config command: {str(e)}")
            raise

    def _validate_path(self, path_str: Optional[str], must_exist: bool = False, create_parents: bool = False) -> Optional[Path]:
        """验证路径安全性"""
        if path_str is None:
            return None

        path = Path(path_str)

        # 规范化路径以防止路径遍历
        try:
            normalized_path = path.resolve()
            root_path = Path.cwd().resolve()

            # 检查是否在当前工作目录下（防止路径遍历）
            normalized_path.relative_to(root_path)
        except ValueError:
            raise ValueError(f"Path traversal detected: {path_str}")
        except RuntimeError:
            # 在某些系统上，resolve() 可能失败
            raise ValueError(f"Cannot resolve path: {path_str}")

        # 检查是否存在
        if must_exist and not normalized_path.exists():
            raise ValueError(f"Path does not exist: {normalized_path}")

        # 创建父目录（如果需要）
        if create_parents:
            try:
                normalized_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise ValueError(f"No permission to create directory: {normalized_path.parent}")

        return normalized_path

    def _convert_to_int(self, value: Any, param_name: str, min_val: int = None, max_val: int = None) -> int:
        """转换为整数并验证范围"""
        try:
            converted = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value for {param_name}: {value}. Expected integer.")

        if min_val is not None and converted < min_val:
            raise ValueError(f"{param_name} must be >= {min_val}, got {converted}")

        if max_val is not None and converted > max_val:
            raise ValueError(f"{param_name} must be <= {max_val}, got {converted}")

        return converted

    def _convert_to_bool(self, value: Any) -> bool:
        """转换为布尔值，支持多种格式"""
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            lower_value = value.lower().strip()
            if lower_value in ('true', '1', 'yes', 'on', 'y'):
                return True
            elif lower_value in ('false', '0', 'no', 'off', 'n'):
                return False
            else:
                raise ValueError(f"Invalid boolean value: {value}. Expected true/false, yes/no, on/off, 1/0.")

        if isinstance(value, int):
            return value != 0

        return bool(value)

    def _parse_api_keys(self, api_keys_str: Optional[str]) -> Optional[List[str]]:
        """解析API密钥字符串"""
        if api_keys_str is None:
            return None

        # 按逗号分割并去除空白
        keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]

        # 验证每个密钥的格式（使用正则表达式）
        api_key_pattern = r'^sk-[a-zA-Z0-9]{10,}$'
        for key in keys:
            if not re.match(api_key_pattern, key):
                raise ValueError(f"Invalid API key format: {key}. Expected format: sk-[alphanumeric]")

        return keys if keys else None
```

## 验证标准

- [ ] 命令参数解析功能实现完整
- [ ] 多种命令支持
- [ ] 类型校验和安全处理
- [ ] 路径安全性验证
- [ ] API密钥格式处理
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 防止路径遍历攻击
- 验证API密钥格式
- 验证输入参数安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12