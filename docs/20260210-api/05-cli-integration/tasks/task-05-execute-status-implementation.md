# execute_status函数实现

## 概述

execute_status函数负责检查osins-llama服务器的实际运行状态，包括验证进程是否存活以及API接口是否可达。函数返回标准化的退出码，便于脚本或自动化工具判断服务状态。

## 实现要求

1. 检查PID文件存在性
2. 读取并验证PID内容合法性
3. 检查进程是否存在
4. 调用API /health 接口检查服务器健康状态
5. 支持debug输出详细信息
6. 捕获异常并返回标准化退出码
7. 提供详细的日志输出
8. 实现标准化的退出码系统
9. 使用专用的日志记录器

## 代码实现

```python
from pathlib import Path
import os
import requests
import logging
import psutil  # 用于跨平台进程状态检测
from urllib.parse import urlparse
import re


def execute_status(pid_file: Path, api_url: str, debug: bool = False) -> int:
    """
    检查 osins-llama 服务器状态

    Args:
        pid_file: PID 文件路径
        api_url: API 地址
        debug: 是否输出调试日志

    Returns:
        int: 标准退出码
            0: 服务正常运行
            1: PID 文件不存在（服务未运行）
            2: PID 文件存在但进程不存在
            3: API 不可达或返回异常
            4: PID 文件内容非法
            5: 其他异常
    """
    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("status")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    try:
        # 检查 PID 文件存在性
        pid_file = pid_file.resolve()
        if not pid_file.exists():
            logger.warning(f"PID file not found: {pid_file}")
            return 1

        # 读取 PID
        try:
            pid = int(pid_file.read_text().strip())
        except Exception:
            logger.error(f"Invalid PID content in file: {pid_file}")
            return 4

        # 检查进程是否存在
        if not psutil.pid_exists(pid):
            logger.warning(f"PID file exists but process {pid} not running")
            return 2
        logger.info(f"Process {pid} is running")

        # 检查 API 健康
        try:
            response = requests.get(f"{api_url}/health", timeout=3)
            if response.status_code == 200:
                logger.info(f"API reachable at {api_url}")
                return 0
            else:
                logger.warning(f"API returned status code {response.status_code}")
                return 3
        except requests.RequestException as e:
            logger.error(f"API check failed: {e}")
            return 3

    except Exception as e:
        logger.exception(f"Unexpected error during status check: {e}")
        return 5


```

## 验证标准

- [ ] PID文件存在性检查
- [ ] PID内容格式验证
- [ ] 进程存在性验证
- [ ] API /health 接口可达性检查
- [ ] 异常处理机制健全
- [ ] 日志输出功能正常
- [ ] 标准化退出码返回
- [ ] 支持debug输出详细信息
- [ ] 标准化退出码系统实现
- [ ] 使用专用日志记录器
- [ ] 退出码含义准确

## 安全考虑

- 使用psutil库进行跨平台进程状态检测
- 捕获和处理异常，防止程序崩溃
- 验证PID文件内容，防止注入攻击
- 验证API URL，防止SSRF攻击

## 依赖项

- requests: 用于API状态检查
- psutil: 用于进程状态检查
- pathlib: 用于路径操作

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-14
- 最后更新: 2026-02-14