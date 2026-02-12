# BusinessLogicExecutor类实现

## 概述

BusinessLogicExecutor类负责协调和执行CLI的核心业务逻辑。

## 实现要求

1. 实现业务逻辑执行功能
2. 协调各个组件的工作
3. 处理命令执行逻辑
4. 实现错误处理机制
5. 提供统一的执行接口

## 代码实现

```python
import json
from typing import Dict, Any


class BusinessLogicExecutor:
    """业务逻辑执行器"""

    def __init__(self, command_parser, log_processor, config_validator, status_checker, security_checker, logger=None):
        self.logger = logger or __import__('logging').getLogger(__name__)
        self.command_parser = command_parser
        self.log_processor = log_processor
        self.config_validator = config_validator
        self.status_checker = status_checker
        self.security_checker = security_checker

    def execute_start_logic(self, args: Dict[str, Any]) -> CommandResult:
        """执行启动逻辑"""
        try:
            self.logger.info("Starting execution of start command")

            # 解析参数
            params = self.command_parser.parse_start_command(args)

            # 验证配置
            validation_errors = self.config_validator.validate_start_config(params)
            if validation_errors:
                error_msg = f"Configuration validation failed: {'; '.join(validation_errors)}"
                self.logger.error(error_msg)
                return CommandResult(
                    success=False,
                    output="",
                    error=error_msg,
                    exit_code=3,
                    execution_time=0.0
                )

            # 检查端口可用性
            if not self.config_validator.validate_server_availability(params.host, params.port):
                error_msg = f"Port {params.port} is already in use"
                self.logger.error(error_msg)
                return CommandResult(
                    success=False,
                    output="",
                    error=error_msg,
                    exit_code=4,
                    execution_time=0.0
                )

            # 执行启动服务
            start_service = container.get(StartService)
            result = start_service.execute(params)

            self.logger.info(f"Start command execution completed with success={result.success}")
            return result

        except Exception as e:
            error_msg = f"Error in start logic: {str(e)}"
            self.logger.error(error_msg)
            return CommandResult(
                success=False,
                output="",
                error=error_msg,
                exit_code=1,
                execution_time=0.0
            )

    def execute_status_logic(self, args: Dict[str, Any]) -> CommandResult:
        """执行状态检查逻辑"""
        try:
            self.logger.info("Starting execution of status command")

            # 解析参数
            params = self.command_parser.parse_status_command(args)

            # 检查进程状态
            process_status = self.status_checker.check_process_status(params.pid_file)

            # 检查API健康状态
            api_status = self.status_checker.check_server_health(params.api_url)

            # 组合结果
            result = {
                'process': process_status,
                'api': api_status
            }

            status_result = CommandResult(
                success=process_status['running'],
                output=json.dumps(result, indent=2),
                error="",
                exit_code=0 if process_status['running'] else 1,
                execution_time=1.0
            )

            self.logger.info(f"Status command execution completed with success={status_result.success}")
            return status_result
        except Exception as e:
            error_msg = f"Error in status logic: {str(e)}"
            self.logger.error(error_msg)
            return CommandResult(
                success=False,
                output="",
                error=error_msg,
                exit_code=1,
                execution_time=0.0
            )

    def execute_stop_logic(self, args: Dict[str, Any]) -> CommandResult:
        """执行停止逻辑"""
        try:
            self.logger.info("Starting execution of stop command")

            # 解析参数
            params = self.command_parser.parse_stop_command(args)

            # 执行停止服务
            stop_service = container.get(StopService)
            result = stop_service.execute(params)

            self.logger.info(f"Stop command execution completed with success={result.success}")
            return result
        except Exception as e:
            error_msg = f"Error in stop logic: {str(e)}"
            self.logger.error(error_msg)
            return CommandResult(
                success=False,
                output="",
                error=error_msg,
                exit_code=1,
                execution_time=0.0
            )

    def execute_logs_logic(self, args: Dict[str, Any]) -> CommandResult:
        """执行日志逻辑"""
        try:
            self.logger.info("Starting execution of logs command")

            lines = args.get('lines', 50)
            log_file = args.get('log_file', Path('./llama.log'))

            # 获取日志内容
            log_content = self.log_processor.tail_log_file(log_file, lines)

            return CommandResult(
                success=True,
                output=log_content,
                error="",
                exit_code=0,
                execution_time=0.5
            )
        except Exception as e:
            error_msg = f"Error in logs logic: {str(e)}"
            self.logger.error(error_msg)
            return CommandResult(
                success=False,
                output="",
                error=error_msg,
                exit_code=1,
                execution_time=0.0
            )
```

## 验证标准

- [ ] 业务逻辑执行功能实现完整
- [ ] 组件协调功能
- [ ] 命令执行逻辑处理
- [ ] 错误处理机制
- [ ] 统一执行接口提供
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 验证参数安全性
- 防止命令注入攻击
- 验证组件调用安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12