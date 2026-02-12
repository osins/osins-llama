# 安全高风险问题修复方案

**文档编号**: 2026021201-security-fix-plan-high-risk  
**最后更新**: 2026-02-12 01:38  
**状态**: 待实施

## 1. 问题概述

根据金融级零信任模型安全审计协议，当前实现存在3个高风险安全问题，必须修复后才能进入金融生产环境。

## 2. 高风险问题详情

### 2.1 未使用 frozen=True 保护关键数据模型
- **风险等级**: 高
- **影响**: 关键数据模型可变，存在运行时篡改风险
- **受影响模块**: 所有核心数据模型（Usage, ErrorResponse, CompletionRequest等）

### 2.2 缺少最大嵌套深度限制
- **风险等级**: 高  
- **影响**: 存在 JSON 炸弹攻击风险，可能导致服务拒绝
- **受影响模块**: 所有 API 请求处理

### 2.3 字符串字段缺少 max_length 限制
- **风险等级**: 高
- **影响**: 内存溢出、注入攻击、DoS 攻击风险
- **受影响模块**: 所有字符串字段（model, prompt, content, name等）

## 3. 修复方案

### 3.1 frozen=True 实施方案

**修改文件**: `src/llama/models/common/usage.py`
```python
class Usage(BaseModel):
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)
    
    model_config = {
        "frozen": True,      # ✅ 新增
        "extra": "forbid"
    }
```

**需要修改的关键模型列表**:
- `common/usage.py` - Usage
- `common/error_response.py` - ErrorResponse
- `legacy/completion_request.py` - CompletionRequest
- `legacy/completion_response.py` - CompletionResponse
- `chat/chat_message.py` - ChatMessage
- `chat/chat_completion_request.py` - ChatCompletionRequest
- `chat/chat_completion_response.py` - ChatCompletionResponse

### 3.2 最大嵌套深度限制实施方案

**新增文件**: `src/llama/utils/security_utils.py`
```python
def validate_nested_depth(data, max_depth=5, current_depth=0):
    """验证数据嵌套深度"""
    if current_depth > max_depth:
        raise ValidationError(f"Maximum nesting depth ({max_depth}) exceeded")
    
    if isinstance(data, dict):
        for value in data.values():
            validate_nested_depth(value, max_depth, current_depth + 1)
    elif isinstance(data, list):
        for item in data:
            validate_nested_depth(item, max_depth, current_depth + 1)
```

**在 API 路由中集成**:
```python
@app.post("/v1/chat/completions")
async def create_chat_completion(request: Request):
    try:
        body = await request.json()
        validate_nested_depth(body, max_depth=5)  # ✅ 新增验证
        chat_request = ChatCompletionRequest(**body)
        # ...继续处理
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {e}")
```

### 3.3 字符串字段 max_length 限制实施方案

**推荐长度限制表**:

| 字段 | 模块 | 推荐 max_length | 理由 |
|------|------|----------------|------|
| model | common | 256 | 模型名称长度限制 |
| prompt | legacy | 8192 | 上下文窗口兼容性 |
| content | chat | 4096 | 单消息内容合理上限 |
| name | chat | 256 | 用户名/角色名限制 |
| function.name | chat | 256 | 函数名长度限制 |
| function.arguments | chat | 4096 | 参数JSON长度限制 |
| tool_call.id | chat | 256 | 工具调用ID长度限制 |

**示例修改**:
```python
class ChatMessage(BaseModel):
    role: str = Field(..., pattern=r"^(system|user|assistant|tool)$")
    content: Optional[str] = Field(default=None, max_length=4096)  # ✅ 新增
    name: Optional[str] = Field(default=None, max_length=256)     # ✅ 新增
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
```

## 4. 实施步骤

### 第一阶段（立即执行）
1. [ ] 修改所有关键模型添加 `frozen=True`
2. [ ] 为所有字符串字段添加 `max_length` 限制
3. [ ] 添加跨字段校验规则（total_tokens = prompt_tokens + completion_tokens）

### 第二阶段（24小时内）
1. [ ] 实现嵌套深度验证工具
2. [ ] 在所有 API 路由中集成验证
3. [ ] 更新单元测试覆盖新验证逻辑

### 第三阶段（48小时内）
1. [ ] 运行完整测试套件
2. [ ] 重新进行安全审计
3. [ ] 更新项目完成度报告

## 5. 验证标准

- [ ] 所有关键模型不可变（尝试赋值应抛出 TypeError）
- [ ] 字符串超长输入应返回 400 错误
- [ ] 嵌套深度超过限制应返回 400 错误
- [ ] 跨字段校验失败应返回 400 错误
- [ ] 所有现有测试用例仍然通过

## 6. 风险评估

| 修复项 | 实施难度 | 影响范围 | 预期效果 |
|--------|----------|----------|----------|
| frozen=True | 低 | 中 | 消除篡改风险 |
| max_length | 低 | 高 | 防止内存溢出 |
| 嵌套深度 | 中 | 高 | 防止 JSON 炸弹 |
| 跨字段校验 | 中 | 中 | 确保数据一致性 |

**总体预期**: 安全评级从 B 级提升到 A 级，满足金融级生产要求。