import subprocess
import psutil
import time
import socket
from typing import Optional


def wait_for_port(host: str, port: int, timeout: float = 30.0) -> bool:
    """
    等待端口监听就绪
    
    Args:
        host: 主机地址
        port: 端口号
        timeout: 超时时间（秒）
    
    Returns:
        bool: 如果端口在超时时间内就绪则返回True，否则返回False
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            # 尝试连接到指定端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)  # 设置短超时
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True
        except socket.gaierror:
            # 如果主机名无法解析，继续等待
            pass
        except OSError:
            # 如果连接失败，继续等待
            pass
        
        time.sleep(0.2)
    
    return False


def find_pid_by_port(port: int) -> Optional[int]:
    """
    通过端口号找到实际监听的进程 PID
    
    Args:
        port: 端口号
    
    Returns:
        int | None: 如果找到监听指定端口的进程则返回PID，否则返回None
    """
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                return conn.pid
    except psutil.AccessDenied:
        # 在某些系统上可能需要管理员权限
        # 尝试通过netstat获取PID
        try:
            result = subprocess.run(
                ["netstat", "-an"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                for line in lines:
                    if f":{port}" in line and "LISTENING" in line:
                        # 解析netstat输出，提取PID（Windows上最后一列通常是PID）
                        parts = line.split()
                        if len(parts) >= 4:
                            # 在Windows上，最后一列通常是PID
                            pid_part = parts[-1]
                            if pid_part.isdigit():
                                return int(pid_part)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
            pass
    
    return None


def find_pids_by_port_range(start_port: int, end_port: int) -> list[int]:
    """
    查找在指定端口范围内的所有监听进程PID
    
    Args:
        start_port: 起始端口
        end_port: 结束端口
    
    Returns:
        list[int]: 监听指定端口范围的进程PID列表
    """
    pids = []
    for port in range(start_port, end_port + 1):
        pid = find_pid_by_port(port)
        if pid is not None and pid not in pids:
            pids.append(pid)
    return pids


def is_process_running(pid: int) -> bool:
    """
    检查指定PID的进程是否在运行
    
    Args:
        pid: 进程ID
    
    Returns:
        bool: 如果进程在运行返回True，否则返回False
    """
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def wait_for_pid_by_port(port: int, timeout: float = 30.0) -> Optional[int]:
    """
    等待指定端口开始监听并返回其PID
    
    Args:
        port: 端口号
        timeout: 超时时间（秒）
    
    Returns:
        int | None: 如果在超时时间内找到监听端口的进程PID则返回，否则返回None
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        pid = find_pid_by_port(port)
        if pid is not None:
            return pid
        time.sleep(0.5)
    
    return None