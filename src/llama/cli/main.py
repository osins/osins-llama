"""Main CLI entry point for osins-llama."""
import click
from pathlib import Path
from typing import Optional
from .start import start
from .stop import stop
from .restart import restart
from .status import status
from .config import config
from .logs import logs
from .health import health
from .context import CLIContext
from ..utils.security_utils import validate_config_path
from src.llama.core.logger_manager import logger


class CircularDependencyError(Exception):
    """循环依赖异常"""
    pass


class UnknownCommandError(Exception):
    """未知命令异常"""
    pass


class MissingDependencyError(Exception):
    """缺失依赖异常"""
    pass


def check_command_dependencies(main_group: click.Group) -> None:
    """检查命令间的依赖关系"""
    dependencies = {
        "restart": ["stop", "start"],
        "status": ["start", "stop"],
        "health": ["start"]
    }

    # 检查是否存在未知命令
    for cmd in dependencies.keys():
        if cmd not in main_group.commands:
            raise UnknownCommandError(f"Unknown command: {cmd}")

    # 检查每个命令的依赖是否都存在
    for cmd, deps in dependencies.items():
        for dep in deps:
            if dep not in main_group.commands:
                raise MissingDependencyError(f"Command '{cmd}' cannot execute. Missing dependencies: {[d for d in deps if d not in main_group.commands]}")

    # 检查循环依赖
    try:
        detect_circular_dependency(dependencies)
    except CircularDependencyError as e:
        raise e


def detect_circular_dependency(dependencies: dict) -> None:
    """
    检测依赖图中的循环依赖
    
    :param dependencies: 依赖关系字典
    """
    from collections import defaultdict

    # 构建邻接表表示的图
    graph = defaultdict(list)
    all_nodes = set()
    
    for node, deps in dependencies.items():
        all_nodes.add(node)
        for dep in deps:
            graph[dep].append(node)  # 依赖关系：dep -> node
            all_nodes.add(dep)

    # 使用拓扑排序检测循环依赖
    in_degree = {node: 0 for node in all_nodes}
    
    # 计算每个节点的入度
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] += 1

    # 找到所有入度为0的节点
    queue = []
    for node in in_degree:
        if in_degree[node] == 0:
            queue.append(node)

    # 拓扑排序
    topo_order = []
    while queue:
        current = queue.pop(0)
        topo_order.append(current)

        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # 如果拓扑排序的结果不包含所有节点，则存在循环依赖
    if len(topo_order) != len(all_nodes):
        # 找到循环路径
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph[node]:
                if neighbor in rec_stack:
                    cycle_start_idx = path.index(neighbor)
                    cycle_path = path[cycle_start_idx:] + [neighbor]
                    raise CircularDependencyError(f"Circular dependency detected: {' -> '.join(cycle_path)}")
                elif neighbor not in visited:
                    dfs(neighbor, path.copy())

            rec_stack.remove(node)
            path.pop()

        for node in all_nodes:
            if node not in visited:
                dfs(node, [])

    # 如果没有找到循环依赖，函数正常结束


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
        logger.debug("Verbose mode enabled")
        logger.debug(f"Configuration file path: {config_path}")


# Register all commands
main.add_command(start)
main.add_command(stop)
main.add_command(restart)
main.add_command(status)
main.add_command(config)
main.add_command(logs)
main.add_command(health)

# 在注册命令后执行依赖检查
check_command_dependencies(main)


if __name__ == '__main__':
    main()