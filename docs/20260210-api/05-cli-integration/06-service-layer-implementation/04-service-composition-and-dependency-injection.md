# 服务编排和依赖注入

## 概述

服务编排和依赖注入模块负责管理服务之间的依赖关系，实现服务的自动装配和统一访问。

## 服务容器

### 服务容器实现

```python
from typing import Dict, Type, Any
from contextlib import contextmanager
import threading


class ServiceContainer:
    """服务容器，用于管理服务依赖"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
        self._lock = threading.RLock()  # 线程安全锁
    
    def register(self, service_class: Type, instance: Any = None, singleton: bool = True, factory: callable = None):
        """注册服务"""
        with self._lock:
            if factory:
                self._factories[service_class] = factory
            elif singleton and instance is None:
                # 延迟初始化单例
                self._singletons[service_class] = service_class
            elif instance:
                self._services[service_class] = instance
    
    def get(self, service_class: Type):
        """获取服务实例"""
        with self._lock:
            if service_class in self._services:
                return self._services[service_class]
            
            if service_class in self._factories:
                # 使用工厂创建实例
                instance = self._factories[service_class]()
                self._services[service_class] = instance
                return instance
            
            if service_class in self._singletons:
                # 初始化单例
                singleton_class = self._singletons[service_class]
                instance = singleton_class(container=self)
                self._services[service_class] = instance
                return instance
            
            raise ValueError(f"Service {service_class.__name__} not registered")
    
    def has(self, service_class: Type) -> bool:
        """检查服务是否已注册"""
        with self._lock:
            return (service_class in self._services or 
                    service_class in self._singletons or 
                    service_class in self._factories)
    
    def reset(self):
        """重置容器"""
        with self._lock:
            self._services.clear()
            self._singletons.clear()
            self._factories.clear()
```

## 服务工厂

### 服务工厂实现

```python
import logging


class ServiceFactory:
    """服务工厂，用于创建服务实例"""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
    
    def create_start_service(self, logger: logging.Logger = None) -> StartService:
        """创建启动服务"""
        process_manager = self.container.get(ProcessManager)
        return StartService(process_manager, logger)
    
    def create_stop_service(self, logger: logging.Logger = None) -> StopService:
        """创建停止服务"""
        process_manager = self.container.get(ProcessManager)
        return StopService(process_manager, logger)
    
    def create_restart_service(self, logger: logging.Logger = None) -> RestartService:
        """创建重启服务"""
        process_manager = self.container.get(ProcessManager)
        return RestartService(process_manager, logger)
    
    def create_status_service(self, logger: logging.Logger = None) -> StatusService:
        """创建状态服务"""
        process_manager = self.container.get(ProcessManager)
        return StatusService(process_manager, logger)
    
    def create_logs_service(self, logger: logging.Logger = None) -> LogsService:
        """创建日志服务"""
        return LogsService(logger)
    
    def create_health_check_service(self, logger: logging.Logger = None) -> HealthCheckService:
        """创建健康检查服务"""
        return HealthCheckService(logger)
    
    def create_config_service(self, logger: logging.Logger = None) -> ConfigService:
        """创建配置服务"""
        return ConfigService(logger)
```

## 依赖注入

### 依赖注入实现

```python
from typing import get_type_hints


class DependencyInjector:
    """依赖注入器"""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
    
    def inject_dependencies(self, instance: Any):
        """注入依赖到实例"""
        # 获取类的类型注解
        hints = get_type_hints(type(instance))
        
        # 为每个类型注解查找并注入服务
        for attr_name, attr_type in hints.items():
            if self.container.has(attr_type):
                service_instance = self.container.get(attr_type)
                setattr(instance, attr_name, service_instance)
    
    def create_with_injection(self, cls, *args, **kwargs):
        """创建实例并注入依赖"""
        # 创建实例
        instance = cls(*args, **kwargs)
        
        # 注入依赖
        self.inject_dependencies(instance)
        
        return instance
```

## 服务编排

### 服务编排器

```python
from typing import List, Tuple
import logging


class ServiceOrchestrator:
    """服务编排器"""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
        self.dependency_graph = {}
        self.logger = logging.getLogger(__name__)
    
    def define_dependency(self, service: Type, depends_on: List[Type]):
        """定义服务依赖关系"""
        self.dependency_graph[service] = depends_on
    
    def _has_cycle(self) -> bool:
        """检测依赖图中是否有循环依赖"""
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            
            if node in self.dependency_graph:
                for neighbor in self.dependency_graph[node]:
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.dependency_graph:
            if node not in visited:
                if dfs(node):
                    return True
        return False
    
    def initialize_services(self):
        """按依赖顺序初始化服务"""
        if self._has_cycle():
            raise ValueError("Circular dependency detected in service graph")
        
        visited = set()
        initialization_order = []
        
        def dfs(service: Type):
            if service in visited:
                return
            visited.add(service)
            
            # 先处理依赖项
            if service in self.dependency_graph:
                for dep in self.dependency_graph[service]:
                    dfs(dep)
            
            # 添加当前服务
            initialization_order.append(service)
        
        # 選历所有注册的服务
        for service_class in list(self.container._singletons.keys()):
            dfs(service_class)
        
        # 按顺序初始化服务
        for service_class in initialization_order:
            if service_class in self.container._singletons:
                try:
                    self.container.get(service_class)
                    self.logger.info(f"Initialized service: {service_class.__name__}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize service {service_class.__name__}: {str(e)}")
                    raise
    
    def execute_with_dependencies(self, service_class: Type, method_name: str, *args, **kwargs):
        """执行服务方法，确保依赖已初始化"""
        try:
            service = self.container.get(service_class)
            method = getattr(service, method_name)
            return method(*args, **kwargs)
        except AttributeError:
            self.logger.error(f"Method {method_name} not found in service {service_class.__name__}")
            raise
        except Exception as e:
            self.logger.error(f"Error executing {service_class.__name__}.{method_name}: {str(e)}")
            raise
```

## 全局容器

### 全局服务容器

```python
# 全局服务容器
container = ServiceContainer()

# 初始化容器
def initialize_container():
    """初始化全局容器"""
    # 注册基础服务
    container.register(ProcessManager)
    container.register(ConfigService)
    
    # 注册命令服务
    container.register(StartService)
    container.register(StopService)
    container.register(RestartService)
    container.register(StatusService)
    container.register(LogsService)
    container.register(HealthCheckService)
    
    # 初始化依赖
    orchestrator = ServiceOrchestrator(container)
    orchestrator.initialize_services()
```

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12