# 安全低风险问题修复方案

**文档编号**: 2026021203-security-fix-plan-low-risk  
**最后更新**: 2026-02-12 01:38  
**状态**: 待实施

## 1. 问题概述

根据金融级零信任模型安全审计协议，当前实现存在2个低风险安全问题，建议修复以完善系统安全性。

## 2. 低风险问题详情

### 2.1 缺少模型 schema 版本跟踪
- **风险等级**: 低
- **影响**: 模型变更无法追溯，版本管理困难
- **具体问题**: 无 schema 哈希或版本标识

### 2.2 缺少模糊测试和恶意输入测试
- **风险等级**: 低
- **影响**: 未充分测试边界情况和对抗攻击
- **具体问题**: 测试覆盖主要为正常流程，缺乏异常场景测试

## 3. 修复方案

### 3.1 模型 schema 版本跟踪实施方案

**新增文件**: `src/llama/utils/schema_version.py`
```python
import hashlib
import json
from typing import Dict, Any

def calculate_schema_hash(schema_dict: Dict[str, Any]) -> str:
    """计算模型 schema 的哈希值"""
    # 移除非确定性字段（如注释、顺序等）
    clean_schema = {
        k: v for k, v in schema_dict.items() 
        if not k.startswith('_') and k not in ['__doc__', '__module__']
    }
    
    # 序列化并计算哈希
    schema_json = json.dumps(clean_schema, sort_keys=True, indent=2)
    return hashlib.sha256(schema_json.encode('utf-8')).hexdigest()

def get_model_schema_version(model_class) -> str:
    """获取模型类的 schema 版本"""
    try:
        # 获取 Pydantic 模型的 schema
        schema = model_class.model_json_schema()
        return calculate_schema_hash(schema)
    except Exception:
        return "unknown"
```

**在 API 响应中添加版本信息**:
```python
# 在健康检查端点中返回版本信息
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "schema_version": get_model_schema_version(ChatCompletionResponse),
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

**在日志中记录 schema 版本**:
```python
# 在启动时记录
logger.info(f"Model schema version: {get_model_schema_version(ChatCompletionResponse)}")
```

### 3.2 模糊测试和恶意输入测试实施方案

**新增测试文件**: `tests/fuzz/test_fuzz_security.py`
```python
import pytest
import random
import string
from src.llama.models.chat.chat_message import ChatMessage

def generate_random_string(length: int) -> str:
    """生成随机字符串用于模糊测试"""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

def test_fuzz_long_strings():
    """测试超长字符串输入"""
    # 测试接近上限的字符串
    long_content = generate_random_string(4097)  # 超过 max_length=4096
    with pytest.raises(Exception):
        ChatMessage(role="user", content=long_content)

def test_fuzz_nested_structures():
    """测试深度嵌套结构"""
    # 构建深度嵌套的 JSON
    nested = {}
    current = nested
    for i in range(10):  # 超过 max_depth=5
        current["child"] = {}
        current = current["child"]
    
    with pytest.raises(Exception):
        # 尝试验证嵌套结构
        validate_nested_depth(nested, max_depth=5)

def test_fuzz_malicious_input():
    """测试恶意输入"""
    # SQL 注入尝试
    malicious_content = "'; DROP TABLE users; --"
    with pytest.raises(Exception):
        ChatMessage(role="user", content=malicious_content)
    
    # XSS 尝试
    xss_content = "<script>alert('xss')</script>"
    with pytest.raises(Exception):
        ChatMessage(role="user", content=xss_content)
```

**添加边界条件测试**:
```python
# tests/unit/test_boundary_conditions.py
def test_boundary_values():
    """测试边界值"""
    # 最小值测试
    usage_min = Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
    assert usage_min.total_tokens == 0
    
    # 最大值测试（接近限制）
    usage_max = Usage(prompt_tokens=8192, completion_tokens=2048, total_tokens=10240)
    assert usage_max.total_tokens == 10240
    
    # 边界溢出测试
    with pytest.raises(Exception):
        Usage(prompt_tokens=-1, completion_tokens=0, total_tokens=0)
```

## 4. 实施步骤

### 第一阶段（48小时内）
1. [ ] 实现模型 schema 版本跟踪
2. [ ] 添加模糊测试框架
3. [ ] 创建恶意输入测试用例

### 第二阶段（72小时内）
1. [ ] 集成到 CI/CD 流程
2. [ ] 添加性能压力测试
3. [ ] 更新文档说明

## 5. 验证标准

- [ ] 健康检查端点返回 schema 版本
- [ ] 模糊测试覆盖各种边界情况
- [ ] 恶意输入测试捕获常见攻击模式
- [ ] 所有测试用例通过

## 6. 风险评估

| 修复项 | 实施难度 | 影响范围 | 预期效果 |
|--------|----------|----------|----------|
| schema 版本跟踪 | 低 | 中 | 改进版本管理 |
| 模糊测试 | 中 | 高 | 提升异常处理能力 |
| 恶意输入测试 | 中 | 高 | 增强安全防护 |

**总体预期**: 完善系统安全性，达到金融级生产环境要求。