# 配置优化总结

## 修改概述

根据 llama-server 标准参数配置示例，对 osins-llama 项目进行了全面优化，使其与 OpenAI 兼容的 API 接口更加规范和灵活。

---

## 主要修改内容

### 1. 上下文长度优化

**目标**: 将上下文长度从 8192/2048 提升到 32768

| 文件 | 修改前 | 修改后 |
|------|--------|--------|
| `src/llama/config/model_config.py` | `n_ctx: int = 8192` | `n_ctx: int = 32768` |
| `src/llama/config/config.py` | `LLAMA_N_CTX="8192"` | `LLAMA_N_CTX="32768"` |
| `src/llama/config/resources_config.py` | `max_prompt_tokens=2048`<br>`max_total_tokens=4096` | `max_prompt_tokens=16384`<br>`max_total_tokens=32768` |
| `src/llama/core/commands/start.py` | `max_prompt_tokens=2048`<br>`max_total_tokens=4096` | `max_prompt_tokens=16384`<br>`max_total_tokens=32768` |

### 2. 支持 `extra_body` 参数

**目标**: 允许传递 top_k、min_p 等非 OpenAI 标准参数到 llama.cpp server

**修改文件**: `src/llama/models/chat/chat_completion_request.py`

```python
# 修改 model_config 允许额外字段
model_config = ConfigDict(extra="allow", frozen=True)

# 新增 extra_body 字段
extra_body: Optional[Dict[str, Any]] = Field(
    default=None, 
    description="Extra parameters for llama.cpp server (e.g., top_k, min_p)"
)
```

### 3. 采样参数默认值优化

**目标**: 与示例对齐，使用更合理的默认值

| 参数 | 修改前 | 修改后 | 说明 |
|------|--------|--------|------|
| `temperature` | 0.8 | 1.0 | 提高生成多样性 |
| `top_p` | 1.0 | 0.95 | 更稳定的核采样 |
| `top_k` | 40 | 64 | 更广泛的候选词 |
| `min_p` | 0.05 | 0.01 | 更宽松的概率阈值 |
| `max_tokens` | 16/1000 | 8192 | 支持更长生成 |

**修改文件**:
- `src/llama/api/open_ai/completion_routes.py`
- `src/llama/models/chat/chat_completion_request.py`

### 4. Token 限制检查优化

**目标**: 移除硬编码的限制，从配置动态读取

| 文件 | 修改前 | 修改后 |
|------|--------|--------|
| `src/llama/api/open_ai/chat_routes.py` | 硬编码 `2048` | 从 `config.resources.max_total_tokens` 读取 |
| `src/llama/api/open_ai/completion_routes.py` | 硬编码 `MAX_CONTEXT_LENGTH=2048` | 从 `config.resources.max_total_tokens` 读取 |

### 5. `extra_body` 参数传递支持

**目标**: 在服务层处理 extra_body 中的参数

**修改文件**: `src/llama/services/chat_service.py`

在 `generate()` 和 `generate_stream()` 方法中添加：

```python
# 合并 extra_body 中的额外参数（如 top_k, min_p 等）
if request.extra_body:
    raw_kwargs.update(request.extra_body)
```

---

## 新增文件

### `USAGE_EXAMPLES.md`

创建了完整的使用示例文档，包含：
- 基本流式/非流式聊天
- 多模态（图片）支持
- 参数详细说明
- 环境变量配置
- 重要注意事项

---

## 使用示例

### 基本使用

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.50.2:31301/v1",
    api_key="any"
)

response = client.chat.completions.create(
    model="any",
    messages=[{"role": "user", "content": "你好"}],
    temperature=1.0,
    top_p=0.95,
    max_tokens=8192,
    stream=True,
    extra_body={
        "top_k": 64,
        "min_p": 0.01,
    }
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## 环境变量支持

所有配置都可以通过环境变量覆盖：

```bash
export LLAMA_N_CTX=32768              # 上下文长度
export LLAMA_MAX_PROMPT_TOKENS=16384  # 最大 prompt tokens
export LLAMA_MAX_TOTAL_TOKENS=32768   # 最大总 tokens
export LLAMA_N_THREADS=8              # 线程数
export LLAMA_N_GPU_LAYERS=16          # GPU 层数
```

---

## 兼容性说明

1. **`top_k` 和 `min_p`**: 必须通过 `extra_body` 传递，直接作为顶层参数会报错
2. **`api_key`**: 填任意字符串，llama-server 不校验
3. **`model`**: 填什么都行，服务器只有一个模型
4. **`stream=True`**: 推荐开启，体验更好

---

## 性能影响

- **上下文长度提升**: 从 2048/4096 提升到 32768，支持更长的对话和文档
- **显存占用**: 更大的上下文会占用更多 GPU 显存，需注意 RTX 3060 12GB 的限制
- **生成质量**: 优化的采样参数（temperature=1.0, top_k=64, min_p=0.01）提供更好的生成质量

---

## 后续建议

1. 监控显存使用情况，确保在 32768 上下文下不会 OOM
2. 根据实际使用场景调整 `max_total_tokens` 限制
3. 考虑添加请求级别的上下文长度控制
4. 更新测试用例以覆盖新的参数配置
