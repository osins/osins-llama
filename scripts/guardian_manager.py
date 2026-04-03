#!/usr/bin/env python
"""Llama服务守护进程管理入口脚本"""
import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llama.services.guardian import GuardianService


def main():
    parser = argparse.ArgumentParser(description='Llama Service Guardian Manager')
    parser.add_argument('action', 
                       choices=['start', 'stop', 'restart', 'status'], 
                       help='Action to perform on the guardian service')
    parser.add_argument('--config', 
                       type=str, 
                       default='./guardian_config.yaml',
                       help='Path to guardian configuration file')
    parser.add_argument('--pid-file',
                       type=str,
                       default='./llama.pid',
                       help='Path to PID file')

    args = parser.parse_args()

    # 设置环境变量
    os.environ['LLAMA_PID_FILE'] = args.pid_file

    if args.action == 'start':
        print("Starting guardian service...")
        guardian = GuardianService(config_path=args.config)
        try:
            guardian.start_service()
        except KeyboardInterrupt:
            print("\nShutting down guardian service...")
            guardian.stop()
    
    elif args.action == 'stop':
        print("Stopping guardian service is not directly supported in this mode.")
        print("Send SIGTERM/SIGINT to the guardian process to stop it gracefully.")
        
    elif args.action == 'status':
        print("Checking guardian service status...")
        # 这里需要根据实际情况实现状态检查
        print("Status checking not fully implemented in this standalone script.")
        
    elif args.action == 'restart':
        print("Restarting guardian service is not directly supported in this mode.")
        print("Please stop the current guardian service and start a new one.")


if __name__ == "__main__":
    main()