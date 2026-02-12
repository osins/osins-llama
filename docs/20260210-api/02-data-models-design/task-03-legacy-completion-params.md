# Legacy Completion Params模型任务文档

## 任务概述
- **任务编号**: 3
- **任务名称**: Legacy Completion Params模型
- **文件路径**: `models/legacy/completion_params.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现CompletionParams数据模型，用于表示Legacy Completion API的通用生成参数。该模型需要严格遵循OpenAI Completions API规范，包含temperature、max_tokens等参数。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 包含以下字段：
  - model: str - 模型名称
  - prompt: Union[str, List[str]] - 提示内容
  - max_tokens: Optional[int] - 最大生成令牌数
  - temperature: Optional[float] - 温度参数
  - 等其他Completion API参数
- 遵循OpenAI API的CompletionParams对象结构
- 使用Pydantic v2语法

## 实现规范
- 遵循OpenAI Completions API参数规范
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法
- API Schema层禁止泛型

## 代码实现
```python
# models/legacy/completion_params.py

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Union, List, Dict, Any
from typing import Literal

class CompletionParams(BaseModel):
    """
    Completion Params 数据模型
    表示 Legacy Completion API 的通用生成参数，严格遵循 OpenAI Completions API 规范。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    model: str
    prompt: Union[str, List[str]]
    max_tokens: Optional[int] = 16
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    logprobs: Optional[int] = None
    echo: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    best_of: Optional[int] = 1
    logit_bias: Optional[Dict[str, Any]] = None
    user: Optional[str] = None
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API的CompletionParams结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)

## 依赖关系
- 无前置依赖

## 备注
此模型为Legacy Completion层的核心参数模型，一旦完成将冻结，只做bugfix。