# CLI主入口函数实现

## 概述

CLI主入口函数是CLI应用的起点，负责初始化命令行界面并注册所有可用命令。

## 实现要求

1. 使用Click库创建CLI应用
2. 实现通用选项（verbose, config等）
3. 注册所有CLI命令
4. 处理命令执行上下文
5. 实现安全校验机制
6. 统一日志管理系统

## 1. 安全校验方案

### 1.1 配置文件路径安全

* 限制配置文件必须在安全目录内，避免路径遍历和符号链接攻击。
* 使用 `os.path.abspath` 解析绝对路径并校验。
* 检查文件权限，确保当前用户有读取权限。
* 增加文件内容格式校验（JSON/YAML schema），避免 CLI 被错误配置破坏服务。

```python
import os
import stat
import click
import json
import yaml

SAFE_CONFIG_DIR = "/etc/osins-llama"

def validate_json_config(path: Path) -> None:
    """校验JSON配置文件内容格式和关键字段"""
    try:
        with path.open('r') as f:
            data = json.load(f)
        # 示例：校验必需字段
        required_fields = ["server_port", "host"]
        for field in required_fields:
            if field not in data:
                raise click.BadParameter(f"Config {path} missing required field '{field}'")
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Config {path} is not a valid JSON file: {e}")

def validate_yaml_config(path: Path) -> None:
    """校验YAML配置文件内容格式和关键字段"""
    try:
        with path.open('r') as f:
            data = yaml.safe_load(f)
        # 示例：校验必需字段
        required_fields = ["server_port", "host"]
        for field in required_fields:
            if field not in data:
                raise click.BadParameter(f"Config {path} missing required field '{field}'")
    except yaml.YAMLError as e:
        raise click.BadParameter(f"Config {path} is not a valid YAML file: {e}")

def validate_config_content(path: Path) -> None:
    """根据文件扩展名选择适当的校验方法"""
    if path.suffix.lower() == '.json':
        validate_json_config(path)
    elif path.suffix.lower() in ['.yaml', '.yml']:
        validate_yaml_config(path)
    else:
        raise click.BadParameter(f"Unsupported config file format: {path.suffix}")

def validate_config_path(ctx: click.Context, param: click.Parameter, value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    abs_path = os.path.abspath(value)
    if not abs_path.startswith(SAFE_CONFIG_DIR):
        raise click.BadParameter(f"Config path {value} is outside of allowed directory.")
    if os.path.islink(abs_path):
        raise click.BadParameter(f"Config path {value} must not be a symbolic link.")
    if not os.path.isfile(abs_path):
        raise click.BadParameter(f"Config path {value} must be a regular file.")
    
    # 检查文件权限
    file_stat = os.stat(abs_path)
    if not bool(file_stat.st_mode & stat.S_IRUSR):
        raise click.BadParameter(f"Config file {value} is not readable by the current user.")
    
    # 校验配置文件内容
    validate_config_content(Path(abs_path))
        
    return abs_path
```

---

### 1.2 上下文对象封装

* 避免使用松散的 `dict`，用类封装 CLI 上下文参数，增加类型安全。
* 在 CLIContext 内统一管理日志输出路径和脱敏策略。

```python
from typing import Optional
from pathlib import Path
import click
import logging

class CLIContext:
    verbose: bool
    config_path: Optional[Path]
    logger: logging.Logger

    def __init__(self, verbose: bool = False, config_path: Optional[Path] = None):
        self.verbose = verbose
        self.config_path = config_path
        self.logger = self._init_logger()
        
        if verbose:
            self.logger.debug("CLIContext initialized with verbose mode")
            self.logger.debug(f"Configuration file path: {mask_sensitive(str(config_path)) if config_path else 'None'}")
            self.logger.debug("Dependency checking and configuration validation completed")

    def _init_logger(self) -> logging.Logger:
        return setup_logging(self.verbose)
```

---

## 2. 日志管理方案

* 使用 `logging` 代替 `click.echo`，支持不同日志级别。
* 所有命令内部统一使用日志系统，保证可追踪和可审计。
* 支持日志文件输出，便于审计。
* 对日志中敏感信息（配置文件路径、PID）进行脱敏处理，防止日志泄露。
* 确保日志目录安全可写，避免日志丢失。

```python
import logging
import os
from pathlib import Path

def ensure_log_dir(path: Path) -> None:
    """确保日志目录存在且可写"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        if not os.access(path, os.W_OK):
            raise PermissionError(f"Cannot write to log directory: {path}")
    except Exception as e:
        raise RuntimeError(f"Failed to prepare log directory {path}: {e}")

def setup_logging(verbose: bool) -> logging.Logger:
    logger = logging.getLogger("osins-llama")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # 避免重复添加处理器
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # 添加文件处理器，便于审计
        try:
            log_dir = Path("/var/log/osins-llama")
            ensure_log_dir(log_dir)
            file_handler = logging.FileHandler(log_dir / "cli.log")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, RuntimeError) as e:
            # 如果无法创建日志文件，仅使用控制台输出并记录错误
            logger.warning(f"Could not create file logger: {e}")
    
    return logger

def mask_sensitive(data: str) -> str:
    """对敏感信息进行脱敏处理，支持路径、PID、URL等"""
    import re
    # 脱敏路径信息
    if "/" in data or "\\" in data:
        parts = data.split(os.sep) if os.sep in data else data.split("/")
        if len(parts) > 1:
            return os.sep.join(["***" if i != len(parts)-1 else parts[i] for i in range(len(parts))])
    # 脱敏可能的PID
    if re.match(r'^\d+$', data) and len(data) < 10:  # 假设PID不超过10位数
        return "***"
    # 脱敏URL中的密码部分
    data = re.sub(r'://[^@]*@', '://***@', data)
    # 脱敏可能的密码或密钥（简单的模式匹配）
    data = re.sub(r'password["\']?\s*[:=]\s*["\']?[\w\d!@#$%^&*()]+["\']?', 'password=***', data)
    data = re.sub(r'key["\']?\s*[:=]\s*["\']?[\w\d]+["\']?', 'key=***', data)
    return data
```

---

## 3. 主入口函数整改

```python
import click
from .start import start
from .stop import stop
from .restart import restart
from .status import status
from .config import config
from .logs import logs
from .health import health

@click.group()
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.option(
    '--config',
    type=click.Path(exists=True),
    callback=validate_config_path,
    help='Specify configuration file path'
)
@click.pass_context
def main(ctx: click.Context, verbose: bool, config: Optional[str]) -> None:
    """CLI for managing osins-llama server."""
    config_path = Path(config) if config else None
    ctx.obj = CLIContext(verbose=verbose, config_path=config_path)
    
    if verbose:
        ctx.obj.logger.debug("Verbose mode enabled")
        ctx.obj.logger.debug(f"Configuration file path: {config_path}")
```

---

## 4. 命令注册

* 所有命令注册保持不变。
* 确保依赖顺序（例如 `restart` 依赖 `stop`，`status` 依赖 `start`/`stop`）。
* 建议在注册前增加依赖检查函数，避免运行时错误。
* 增加启动时依赖完整性检查，防止命令调用时缺失依赖。

```python
def check_command_dependencies(main_group: click.Group) -> None:
    """检查命令间的依赖关系"""
    dependencies = {
        "restart": ["stop"],
        "status": ["start", "stop"]
    }

    for cmd, deps in dependencies.items():
        for dep in deps:
            if dep not in main_group.commands:
                raise RuntimeError(f"Command '{cmd}' depends on '{dep}' which is not registered")

# 在注册命令前执行依赖检查
check_command_dependencies(main)

main.add_command(start)
main.add_command(stop)
main.add_command(restart)
main.add_command(status)
main.add_command(config)
main.add_command(logs)
main.add_command(health)
```

---

## 5. 验收标准改进

| 项目     | 改进措施                          |
| ------ | ----------------------------- |
| 配置文件安全 | 路径遍历、符号链接、文件类型、文件权限检查，限制安全目录            |
| 日志记录   | 使用统一 logging，支持 verbose 模式，支持文件输出    |
| 上下文管理  | 用 CLIContext 封装，类型安全          |
| 命令依赖   | 检查命令顺序，确保依赖关系正确               |
| 类型注解   | ctx, verbose, config, callback 参数均有完整类型注解，兼容 Python 3.9 及以上版本 |
| 安全防护   | 后续命令需校验所有文件、PID、路径输入          |

---

## 6. 建议

* 后续每个命令实现都应继承安全策略：

  * 路径/文件输入校验
  * PID 操作安全
  * 日志记录和脱敏
* CLIContext 可扩展，存放更多全局共享对象（例如配置、状态缓存）。
* 对 `verbose` 模式下打印更多上下文信息，便于调试。
* 对路径、PID、日志等敏感信息可添加脱敏策略。
* 为未来扩展 CLIContext（缓存、状态、全局配置）预留接口。
* 对 CLI 中的所有路径、PID、文件操作统一做安全检查，形成基础类/工具函数复用。
* 在日志输出中对敏感信息（路径、PID、配置内容）进行脱敏处理，防止日志泄露。
* CLIContext 可以扩展全局缓存、状态、配置对象，便于多命令共享。
* 对 CLI 内的所有路径、PID、文件操作形成工具类/基础函数，保证复用和安全。
* 对 `verbose` 模式下增加上下文、依赖检查信息打印，便于调试。
* CLIContext 可扩展为全局状态管理类，存放配置对象、缓存数据、命令执行状态和日志统一处理。
* 所有命令内部应继承 CLIContext 的日志和安全策略，避免重复实现。

## 7. 统一工具模块

为提高代码复用性和一致性，建议创建统一的工具模块，包含：

* 日志工具：`setup_logging`, `mask_sensitive`
* 配置校验：`validate_config_content`, `validate_json_config`, `validate_yaml_config`
* 路径安全：`ensure_log_dir`, `validate_config_path`
* 依赖检查：`check_command_dependencies`

```python
# utils/cli_tools.py
from .logging_utils import setup_logging, mask_sensitive
from .config_validator import validate_config_content, validate_json_config, validate_yaml_config
from .security_utils import ensure_log_dir, validate_config_path
from .dependency_checker import check_command_dependencies
```

## 8. CLIContext 扩展建议

CLIContext 可进一步扩展为全局状态管理类，包含以下组件：

* 配置对象：解析并存储 JSON/YAML 配置内容
* 缓存数据：临时存储命令间共享的数据
* 命令执行状态：跟踪各命令执行情况
* 日志统一处理：提供统一的日志接口给所有命令使用
* 安全策略：为所有命令提供一致的安全检查机制

```python
class CLIContext:
    def __init__(self, verbose: bool = False, config_path: Optional[Path] = None):
        self.verbose = verbose
        self.config_path = config_path
        self.config_data = self._load_config_data()  # 解析配置文件
        self.cache = {}  # 临时缓存
        self.command_status = {}  # 命令执行状态
        self.logger = self._init_logger()
        
        if verbose:
            self.logger.debug("CLIContext initialized with verbose mode")
            self.logger.debug(f"Configuration file path: {mask_sensitive(str(config_path)) if config_path else 'None'}")
            self.logger.debug("Dependency checking and configuration validation completed")

    def _load_config_data(self):
        """加载并解析配置文件数据"""
        if self.config_path and self.config_path.exists():
            if self.config_path.suffix.lower() == '.json':
                import json
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            elif self.config_path.suffix.lower() in ['.yaml', '.yml']:
                import yaml
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
        return {}
```

## 验证标准

- [ ] 函数能够正确接收命令行参数
- [ ] 通用选项功能正常
- [ ] 所有命令正确注册
- [ ] 上下文传递正常
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 配置文件路径安全校验功能正常
- [ ] 日志系统按预期工作
- [ ] 上下文对象封装有效

## 安全考虑

- 验证配置文件路径安全性
- 防止路径遍历攻击
- 验证输入参数格式
- 避免符号链接攻击
- 使用安全的日志记录机制

## 版本信息
- 版本: 2.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-13