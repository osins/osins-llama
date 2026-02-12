# 安全中风险问题修复方案

**文档编号**: 2026021202-security-fix-plan-medium-risk  
**最后更新**: 2026-02-12 01:38  
**状态**: 待实施

## 1. 问题概述

根据金融级零信任模型安全审计协议，当前实现存在3个中风险安全问题，建议修复以提升系统安全性。

## 2. 中风险问题详情

### 2.1 缺少跨字段校验规则
- **风险等级**: 中
- **影响**: 数据一致性无法保证，可能导致业务逻辑错误
- **具体问题**: usage.total_tokens 与 prompt_tokens + completion_tokens 不一致

### 2.2 未使用 exclude_none=True 减少数据泄露
- **风险等级**: 中
- **影响**: 响应中可能包含 None 字段，增加数据泄露风险
- **具体问题**: Pydantic 序列化时未过滤 None 值

### 2.3 缺少 mypy 严格模式检查
- **风险等级**: 中
- **影响**: 类型系统不够严谨，可能存在类型相关漏洞
- **具体问题**: 未启用 mypy 的 strict 模式检查

## 3. 修复方案

### 3.1 跨字段校验规则实施方案

**修改文件**: `src/llama/models/common/usage.py`
```python
class Usage(BaseModel):
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)
    
    @field_validator('total_tokens', mode='before')
    @classmethod
    def validate_total_tokens(cls, v, info):
        if 'prompt_tokens' in info.data and 'completion_tokens' in info.data:
            expected = info.data['prompt_tokens'] + info.data['completion_tokens']
            if v != expected:
                raise ValueError(f"total_tokens ({v}) must equal prompt_tokens + completion_tokens ({expected})")
        return v
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
```

**其他跨字段校验**:
- `finish_reason` 与响应状态一致性验证
- `tool_calls` 与 `content` 互斥性验证

### 3.2 exclude_none=True 实施方案

**修改所有模型配置**:
```python
model_config = {
    "frozen": True,
    "extra": "forbid",
    "exclude_none": True  # ✅ 新增
}
```

**在 API 响应中统一应用**:
```python
# 在服务层统一处理
def serialize_response(model: BaseModel) -> dict:
    """序列化响应，排除 None 值"""
    return model.model_dump(exclude_none=True)

# 或者在 FastAPI 中全局配置
app = FastAPI(
    title="osins-llama API",
    version="1.0.0",
    default_response_class=ORJSONResponse
)

# 在每个路由中使用
return ChatCompletionResponse(**response_data).model_dump(exclude_none=True)
```

### 3.3 mypy 严格模式检查实施方案

**修改 pyproject.toml**:
```toml
[tool.mypy]
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_unreachable = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
implicit_reexport = false
strict_equality = true
```

**添加 mypy 配置文件**: `mypy.ini`
```ini
[mypy]
mypy_path = src
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_unreachable = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
implicit_reexport = false
strict_equality = true
```

**添加 CI 检查**:
```yaml
# .github/workflows/mypy.yml
name: MyPy Type Checking
on: [push, pull_request]
jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    - name: Run MyPy
      run: mypy src/ tests/
```

## 4. 实施步骤

### 第一阶段（24小时内）
1. [ ] 实现跨字段校验规则
2. [ ] 在所有模型中添加 `exclude_none=True`
3. [ ] 配置 mypy 严格模式

### 第二阶段（48小时内）
1. [ ] 更新测试用例覆盖新校验逻辑
2. [ ] 添加 mypy CI 检查
3. [ ] 运行完整类型检查

## 5. 验证标准

- [ ] 跨字段不一致输入返回 400 错误
- [ ] 响应中不包含 None 字段
- [ ] mypy 严格模式检查通过
- [ ] 所有现有测试用例仍然通过

## 6. 风险评估

| 修复项 | 实施难度 | 影响范围 | 预期效果 |
|--------|----------|----------|----------|
| 跨字段校验 | 中 | 中 | 确保数据一致性 |
| exclude_none | 低 | 高 | 减少数据泄露 |
| mypy 严格模式 | 中 | 高 | 提升类型安全性 |

**总体预期**: 消除中风险问题，为进入金融生产环境做好准备。