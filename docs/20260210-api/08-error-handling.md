# 错误处理开发指南

## 概述

错误处理是确保系统稳定性和用户体验的关键环节。本指南详细描述了错误处理的策略、类型、实现和最佳实践，确保系统在各种异常情况下都能提供有意义的反馈。

## 错误处理原则

### 1. 容错性
- 系统应在出现错误时继续运行
- 提供降级功能
- 避免级联故障

### 2. 透明性
- 提供清晰的错误信息
- 保持错误上下文
- 便于问题诊断

### 3. 一致性
- 统一的错误响应格式
- 标准化的错误码
- 一致的处理流程

### 4. 安全性
- 不泄露系统内部信息
- 保护敏感数据
- 防止信息泄露攻击

## 错误分类

### 1. 客户端错误 (4xx)
- `400 Bad Request` - 请求格式错误或参数无效
- `401 Unauthorized` - 未提供或无效的身份验证
- `403 Forbidden` - 访问被拒绝
- `404 Not Found` - 请求的资源不存在
- `422 Unprocessable Entity` - 请求格式正确但语义错误
- `429 Too Many Requests` - 请求过于频繁，触发限流

### 2. 服务器错误 (5xx)
- `500 Internal Server Error` - 服务器内部错误
- `502 Bad Gateway` - 网关错误
- `503 Service Unavailable` - 服务暂时不可用
- `504 Gateway Timeout` - 网关超时

## 错误响应格式

### 统一错误响应结构
```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "错误描述信息",
    "code": "error_code",
    "param": "相关参数（可选）"
  }
}
```

### 错误类型定义
- `invalid_request_error` - 无效请求错误
- `authentication_error` - 认证错误
- `permission_error` - 权限错误
- `rate_limit_error` - 速率限制错误
- `overloaded_error` - 系统过载错误
- `server_error` - 服务器内部错误

## 异常层次结构

### 1. 基础异常类
```python
class LLMServiceException(Exception):
    """基础异常类"""
    def __init__(self, message: str, error_type: str, code: str, param: str = None):
        self.message = message
        self.error_type = error_type
        self.code = code
        self.param = param
        super().__init__(message)
```

### 2. 客户端异常类
```python
class InvalidRequestError(LLMServiceException):
    """无效请求异常"""
    def __init__(self, message: str, param: str = None):
        super().__init__(message, "invalid_request_error", "invalid_request", param)

class AuthenticationError(LLMServiceException):
    """认证异常"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "authentication_error", "authentication_error")

class RateLimitError(LLMServiceException):
    """速率限制异常"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "rate_limit_error", "rate_limit_exceeded")
```

### 3. 服务器异常类
```python
class ModelNotFoundError(LLMServiceException):
    """模型未找到异常"""
    def __init__(self, model_name: str):
        super().__init__(f"Model '{model_name}' not found", "server_error", "model_not_found")

class ContextOverflowError(LLMServiceException):
    """上下文溢出异常"""
    def __init__(self, message: str = "Context length exceeds maximum limit"):
        super().__init__(message, "invalid_request_error", "context_overflow")

class InternalServerError(LLMServiceException):
    """内部服务器异常"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, "server_error", "internal_error")
```

## 错误处理策略

### 1. 服务层错误处理
- 捕获底层异常并转换为业务异常
- 维护错误上下文信息
- 实现重试机制（如适用）

### 2. API层错误处理
- 使用FastAPI的exception_handler统一处理
- 返回标准化错误响应
- 记录错误日志

### 3. 中间件错误处理
- 认证中间件错误处理
- 限流中间件错误处理
- 日志中间件错误处理

## 全局异常处理器

### 实现示例
```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(LLMServiceException)
async def llm_service_exception_handler(request: Request, exc: LLMServiceException):
    """全局LLM服务异常处理器"""
    return JSONResponse(
        status_code=get_http_status_code(exc.error_type),
        content={
            "error": {
                "type": exc.error_type,
                "message": exc.message,
                "code": exc.code,
                "param": exc.param
            }
        }
    )

def get_http_status_code(error_type: str) -> int:
    """根据错误类型返回HTTP状态码"""
    status_map = {
        "invalid_request_error": 400,
        "authentication_error": 401,
        "permission_error": 403,
        "rate_limit_error": 429,
        "server_error": 500
    }
    return status_map.get(error_type, 500)
```

## 常见错误场景及处理

### 1. 模型相关错误
- 模型文件不存在或无法加载 → 返回404或500
- 模型格式不支持 → 返回400
- 模型路径非法 → 返回400

### 2. 参数相关错误
- 必需参数缺失 → 返回400
- 参数类型错误 → 返回400
- 参数值超出有效范围 → 返回400
- 互斥参数同时提供 → 返回400

### 3. 认证授权错误
- API密钥缺失或无效 → 返回401
- API密钥权限不足 → 返回403
- 认证令牌过期 → 返回401

### 4. 资源限制错误
- 并发请求超限 → 返回429
- 速率限制触发 → 返回429
- 内存不足 → 返回503
- 上下文长度超出限制 → 返回400

## 日志记录策略

### 1. 错误日志级别
- `DEBUG` - 详细的错误调试信息
- `INFO` - 一般错误信息
- `WARNING` - 可能影响服务的错误
- `ERROR` - 影响服务功能的错误
- `CRITICAL` - 严重错误，可能导致服务崩溃

### 2. 日志内容
- 错误时间戳
- 错误类型和代码
- 错误描述信息
- 请求相关信息（ID、路径、方法）
- 用户相关信息（IP、API密钥标识）

### 3. 敏感信息处理
- 不在日志中记录敏感信息
- 对API密钥进行脱敏
- 过滤个人身份信息

## 重试和恢复机制

### 1. 自动重试
- 对于临时性错误实现重试机制
- 设置重试次数和间隔
- 避免对幂等性不安全的操作进行重试

### 2. 降级策略
- 当部分功能不可用时提供降级服务
- 维持核心功能的可用性
- 向用户明确说明降级状态

### 3. 熔断机制
- 使用熔断器防止级联故障
- 实现健康检查和自动恢复
- 临时隔离故障组件

## 限流错误处理

### 1. 速率限制
- 基于IP或API密钥的请求频率限制
- 返回429状态码和重试时间
- 在响应头中提供限流信息

### 2. 并发限制
- 限制同时处理的请求数量
- 队列等待机制
- 请求超时处理

## 流式响应错误处理

### 1. 客户端断开
- 检测客户端连接断开
- 及时取消后台任务
- 释放占用的资源

### 2. 生成过程错误
- 在流式生成过程中发生错误时立即终止
- 发送错误信息到客户端
- 清理临时资源

## 错误测试

### 1. 单元测试
- 测试各种错误场景
- 验证错误响应格式
- 检查异常处理逻辑

### 2. 集成测试
- 模拟错误条件
- 验证错误传播
- 检查错误恢复

### 3. 错误注入测试
- 主动注入错误
- 验证系统响应
- 测试恢复能力

## 监控和告警

### 1. 错误率监控
- 统计各类错误的发生频率
- 设置错误率阈值告警
- 分析错误趋势

### 2. 性能影响监控
- 监控错误对性能的影响
- 识别高频错误
- 优化常见错误处理

### 3. 告警机制
- 错误率超标告警
- 严重错误即时告警
- 错误趋势异常告警

## 错误处理最佳实践

### 1. 设计原则
- 提供清晰、有用的错误消息
- 保护敏感信息不泄露到错误消息
- 统一错误响应格式
- 记录足够的错误信息用于调试

### 2. 实现建议
- 实现适当的错误恢复机制
- 定期审查和优化错误处理逻辑
- 对错误处理代码进行充分测试
- 保持错误处理逻辑的简洁性

### 3. 维护考虑
- 建立错误分类体系
- 定期分析错误日志
- 优化常见错误路径
- 保持错误码的向后兼容性

## 错误码管理

### 1. 错误码定义
- 使用有意义的错误码命名
- 维护错误码映射表
- 提供错误码说明文档

### 2. 错误码分类
- 客户端错误码 (如: invalid_request, authentication_error)
- 服务器错误码 (如: server_error, model_not_found)
- 业务逻辑错误码 (如: context_overflow, rate_limit_exceeded)

### 3. 错误码演进
- 保持向后兼容
- 提供错误码变更日志
- 通知用户错误码变化

## 安全考虑

### 1. 信息泄露防护
- 避免在错误消息中泄露系统内部信息
- 过滤堆栈跟踪信息
- 防止时序攻击

### 2. 错误枚举防护
- 限制错误信息的详细程度
- 防止通过错误信息推断系统结构
- 统一错误响应格式

## 总结

通过实施全面的错误处理策略，我们可以确保系统在面对各种异常情况时仍能提供稳定可靠的服务。关键是要保持错误处理的一致性、安全性和用户友好性，同时确保有足够的信息用于问题诊断和解决。