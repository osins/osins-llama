#!/usr/bin/env python
"""守护进程启动脚本"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.llama.services.guardian import GuardianService


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Llama Service Guardian')
    parser.add_argument('--config', type=str, help='Configuration file path')
    
    args = parser.parse_args()
    
    guardian = GuardianService(config_path=args.config)
    
    try:
        guardian.start_service()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down guardian service...")
        guardian.stop()


if __name__ == "__main__":
    main()