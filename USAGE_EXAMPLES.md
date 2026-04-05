# osins-llama 使用示例

本文档介绍如何使用 osins-llama 的 OpenAI 兼容 API 进行文本生成。

## 基本配置

- **上下文长度 (n_ctx)**: 32768 tokens
- **最大生成 tokens**: 8192
- **默认 temperature**: 1.0
- **默认 top_p**: 0.95
- **默认 top_k**: 64
- **默认 min_p**: 0.01

---

## 基本聊天完成（流式）

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.50.2:31301/v1",  # 你的服务器地址
    api_key="any"  # llama-server 不验证 key，随便填
)

response = client.chat.completions.create(
    model="any",  # 随便填，llama-server 忽略这个字段
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
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

## 基本聊天完成（非流式）

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.50.2:31301/v1",
    api_key="any"
)

response = client.chat.completions.create(
    model="any",
    messages=[
        {"role": "user", "content": "请写一首关于春天的诗"}
    ],
    temperature=1.0,
    top_p=0.95,
    max_tokens=2048,
    stream=False,
    extra_body={
        "top_k": 64,
        "min_p": 0.01,
    }
)

print(response.choices[0].message.content)
```

---

## 带图片（多模态）

```python
import base64
from openai import OpenAI

# 读取图片并转换为 base64
with open("image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

client = OpenAI(
    base_url="http://192.168.50.2:31301/v1",
    api_key="any"
)

response = client.chat.completions.create(
    model="any",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                        # 或者直接使用 URL
                        # "url": "https://example.com/image.jpg"
                    }
                },
                {
                    "type": "text",
                    "text": "描述这张图片"
                }
            ]
        }
    ],
    max_tokens=8192,
    stream=True,
    extra_body={"top_k": 64, "min_p": 0.01}
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## 关键参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | str | 任意 | llama-server 只有一个模型，此字段会被忽略 |
| `api_key` | str | 任意 | llama-server 不校验 API key |
| `temperature` | float | 1.0 | 采样温度，范围 0.0-2.0 |
| `top_p` | float | 0.95 | 核采样参数，范围 0.0-1.0 |
| `top_k` | int | 64 | Top-k 采样，需放在 `extra_body` 中 |
| `min_p` | float | 0.01 | 最小概率阈值，需放在 `extra_body` 中 |
| `max_tokens` | int | 8192 | 最大生成 token 数 |
| `max_completion_tokens` | int | None | 与 max_tokens 同义 |
| `stream` | bool | False | 是否启用流式输出 |
| `stop` | str/list | None | 停止生成的字符串 |
| `presence_penalty` | float | 0.0 | 存在惩罚，范围 -2.0-2.0 |
| `frequency_penalty` | float | 0.0 | 频率惩罚，范围 -2.0-2.0 |

---

## 重要注意事项

### 1. `extra_body` 的使用

OpenAI 标准 API 不支持 `top_k` 和 `min_p` 参数，因此必须通过 `extra_body` 传递：

```python
# ✅ 正确
response = client.chat.completions.create(
    model="any",
    messages=[...],
    extra_body={
        "top_k": 64,
        "min_p": 0.01,
    }
)

# ❌ 错误 - 会报错
response = client.chat.completions.create(
    model="any",
    messages=[...],
    top_k=64,  # 不支持
    min_p=0.01,  # 不支持
)
```

### 2. `api_key` 配置

llama-server 不验证 API key，可以填任意字符串：

```python
client = OpenAI(
    base_url="http://192.168.50.2:31301/v1",
    api_key="any"  # 或者 "your-api-key-here"，不会被验证
)
```

### 3. `model` 字段

服务器只有一个模型，`model` 字段会被忽略：

```python
# 这些都可以
model="Gemma-4-E4B"
model="any"
model="my-model"
```

### 4. 流式输出推荐

推荐使用 `stream=True`，体验更好：

```python
# 推荐 - 流式
response = client.chat.completions.create(
    model="any",
    messages=[...],
    stream=True,
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## 环境变量配置

可以通过环境变量覆盖默认配置：

```bash
# 上下文长度（默认 32768）
export LLAMA_N_CTX=32768

# 最大 prompt tokens（默认 16384）
export LLAMA_MAX_PROMPT_TOKENS=16384

# 最大总 tokens（默认 32768）
export LLAMA_MAX_TOTAL_TOKENS=32768

# 温度（默认 1.0）
export LLAMA_TEMPERATURE=1.0

# 线程数（默认 8）
export LLAMA_N_THREADS=8

# GPU 层数（默认 16）
export LLAMA_N_GPU_LAYERS=16
```

---

## 完整参数示例

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.50.2:31301/v1",
    api_key="any"
)

response = client.chat.completions.create(
    model="Gemma-4-E4B",
    messages=[
        {"role": "system", "content": "你是一个有用的助手"},
        {"role": "user", "content": "解释一下量子计算"}
    ],
    temperature=1.0,
    top_p=0.95,
    max_tokens=8192,
    stream=True,
    stop=["\n\n", "结束"],
    presence_penalty=0.0,
    frequency_penalty=0.0,
    extra_body={
        "top_k": 64,
        "min_p": 0.01,
    }
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```
