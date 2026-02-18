# API 开发规范

## 代码风格规范 (PEP 8)

### 命名约定
- 模块名: 使用小写字母，单词间可用下划线 (e.g., `completion_request.py`)
- 类名: 使用 PascalCase (e.g., `CompletionRequest`)
- 函数和变量名: 使用 snake_case (e.g., `create_completion`)
- 常量: 使用大写字母和下划线 (e.g., `DEFAULT_PORT = 31301`)

### 代码布局
- 使用 4 个空格缩进，不允许 Tab 字符
- 每行最大长度 79 字符
- 导入语句按标准库、第三方库、本地库分组，每组之间空一行
- 类和函数定义之间空两行

### 其他约定
- 布尔值比较应显式 (e.g., `if flag is True:` 而非 `if flag:`)
- 使用空格分隔操作符 (e.g., `x = 1 + 2`)

## 文档字符串规范 (PEP 257)

### 模块级文档字符串
```python
"""模块功能描述

详细说明模块的用途、功能和使用方法。
"""
```

### 类级文档字符串
```python
class ClassName:
    """类功能描述

    详细说明类的职责、属性和方法。
    """
```

### 函数级文档字符串
```python
def function_name(param1: str, param2: int) -> bool:
    """函数功能描述

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值的描述

    Raises:
        可能抛出的异常
    """
```

## 类型注解规范 (PEP 484 + PEP 526)

### 变量类型注解
```python
# PEP 526 风格的变量注解
variable: str = "initial value"
count: int
items: List[str]
mapping: Dict[str, int]
optional_value: Optional[str] = None
```

### 函数类型注解
```python
from typing import List, Dict, Optional, Union, Generic, TypeVar

T = TypeVar('T')

def process_items(items: List[str]) -> Dict[str, int]:
    """处理项目列表并返回字典"""
    pass

def generic_function(value: T) -> T:
    """泛型函数示例"""
    pass
```

### 类型别名
```python
from typing import NewType

UserId = NewType('UserId', int)
CompletionData = Dict[str, Union[str, int, float]]
```

## 包管理与版本控制规范 (PEP 440 + PEP 345/376)

### 版本号格式 (PEP 440)
- 使用 X.Y.Z 格式 (主版本.次版本.修订版本)
- 可选预发布标签: alpha (aX), beta (bX), release candidate (rcX)
- 示例: 1.0.0, 1.0.0a1, 1.0.0b2, 1.0.0rc3

### 依赖声明 (PEP 345)
- 在 pyproject.toml 中声明依赖
- 使用兼容版本运算符: >=, ~=, ==
- 示例: `fastapi>=0.100.0,<1.0.0`

### 元数据规范 (PEP 376)
- 包含适当的作者、许可证、描述信息
- 分类器应准确反映包的状态和兼容性

## 项目特定规范

### 文件组织
- 每个类和函数必须单独一个 .py 文件
- 绝对不允许在一个 .py 文件中出现两个或两个以上的类或函数
- 使用有意义的目录结构
- 保持一致的导入模式

### API 响应格式
- 严格遵循 OpenAI API 响应格式
- 不得自定义响应数据结构
- **API 响应字段必须与 OpenAI 官方 API 完全匹配**，包括字段名、类型、可选性
- 保持与 OpenAI API 的完全兼容性

### 错误处理
- 使用适当的 HTTP 状态码
- 提供有意义的错误消息
- 遵循 OpenAI API 错误响应格式

### 测试
- 为每个模块编写单元测试
- 使用 pytest 框架
- **测试覆盖率要求 ≥ 90%**，确保核心功能得到充分验证
- **必须严格遵守单元测试开发规范**: [单元测试开发规范](20260210-unit-test-specification.md)

### CI/CD 自动化校验
- **测试覆盖率自动检查**: CI流程中自动验证测试覆盖率 ≥ 90%
- **API 响应一致性自动校验**: 自动对比API响应与OpenAI官方API字段结构
- **代码风格自动检查**: 自动执行PEP 8、PEP 257、PEP 484规范检查
- **类型检查**: 自动执行mypy类型验证

### 术语使用规范
- 避免单独使用"模型"(Model)一词，以防止AI模型与领域模型之间的混淆
- 应当使用明确的术语：
  - "AI模型"或"LLM"指代人工智能语言模型
  - "领域模型"指代业务逻辑中的实体和概念模型
  - "数据模型"指代数据结构定义

## 规范执行说明

本规范为生产环境的 API 开发标准，所有开发者必须严格遵守。规范的目的是确保代码质量、可维护性、以及与 OpenAI API 的完全兼容性。违反规范的代码将无法通过 CI/CD 流程，不得合并到主分支。