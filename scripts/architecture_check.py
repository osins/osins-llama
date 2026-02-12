#!/usr/bin/env python
"""
架构检查脚本
用于验证代码分层隔离规则，确保没有非法的跨层依赖
"""

import ast
import os
from pathlib import Path
from typing import List, Set


class LayerChecker(ast.NodeVisitor):
    """检查代码中的非法导入"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports = []
        self.violations = []
        
    def visit_Import(self, node):
        for alias in node.names:
            module = alias.name
            self._check_import(module, node.lineno)
            
    def visit_ImportFrom(self, node):
        if node.module:
            self._check_import(node.module, node.lineno)
    
    def _check_import(self, module: str, lineno: int):
        """检查导入是否违反分层规则"""
        # 解析模块路径
        parts = module.split('.')
        
        # 检查 api 层不能直接访问 core 或 utils
        if 'src/llama/api/' in self.file_path and len(parts) > 1:
            if parts[1] in ['core', 'utils']:
                self.violations.append(
                    f"API layer cannot import from {module} (line {lineno})"
                )
        
        # 检查 models 层不能依赖 services
        if 'src/llama/models/' in self.file_path and 'services' in parts:
            self.violations.append(
                f"Models layer cannot import from {module} (line {lineno})"
            )
        
        # 检查 core 层不能依赖 api
        if 'src/llama/core/' in self.file_path and 'api' in parts:
            self.violations.append(
                f"Core layer cannot import from {module} (line {lineno})"
            )
        
        # 检查 middlewares 层不能依赖 services
        if 'src/llama/middlewares/' in self.file_path and 'services' in parts:
            self.violations.append(
                f"Middlewares layer cannot import from {module} (line {lineno})"
            )


def check_architecture(src_dir: str = "src"):
    """检查整个项目的架构合规性"""
    violations = []
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read())
                        checker = LayerChecker(file_path)
                        checker.visit(tree)
                        
                        if checker.violations:
                            violations.extend([
                                f"{file_path}: {violation}" 
                                for violation in checker.violations
                            ])
                    except SyntaxError:
                        print(f"Syntax error in {file_path}")
                        continue
    
    return violations


def main():
    print("Checking architecture compliance...")
    violations = check_architecture()
    
    if violations:
        print("Architecture violations found:")
        for violation in violations:
            print(f"  - {violation}")
        return 1
    else:
        print("Architecture check passed!")
        return 0


if __name__ == "__main__":
    exit(main())