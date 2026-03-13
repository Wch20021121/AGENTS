# AGENTS.md

本文件为 AI 编码助手提供项目指南，帮助理解和维护代码库。

## 项目概述

这是一个基于 Python 的 AI 对话助手项目，支持与 OpenAI 兼容的 API 进行交互，并将对话历史以 Markdown 格式持久化存储。

### 核心文件

- `main.py` - 程序入口，处理用户交互
- `chatbot.py` - AIChatbot 类，封装 API 调用逻辑
- `memory.py` - Memory 类，管理对话历史的存储与加载
- `config.py` - 配置管理，初始化环境变量
- `.env` - 环境变量配置文件
- `config/models.txt` - 模型列表配置文件

---

## 环境配置与依赖

### 环境变量

项目使用 `.env` 文件管理敏感配置：

```
API_KEY=your-api-key-here
BASE_URL=https://api.openai.com/v1
MODELS_PATH=config/models.txt
```

**配置说明：**
- `API_KEY` - API 密钥
- `BASE_URL` - API 基础地址
- `MODELS_PATH` - 模型配置文件路径

**重要：** 请勿将 `.env` 文件提交到版本控制系统。

### 依赖安装

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install requests python-dotenv
```

---

## 构建与运行命令

### 运行程序

```bash
# 直接运行
python main.py
```

### 代码检查

```bash
# 使用 ruff 进行 lint 检查
ruff check .

# 使用 ruff 进行格式化
ruff format .

# 类型检查（如使用 mypy）
mypy .
```

### 测试

```bash
# 运行所有测试
pytest

# 运行单个测试文件
pytest tests/test_chatbot.py

# 运行单个测试函数
pytest tests/test_chatbot.py::test_chat -v
```

---

## 代码风格指南

### 导入规范

导入按以下顺序组织，各组之间空一行：

```python
# 1. 标准库
import os
import re
from pathlib import Path
from datetime import datetime

# 2. 第三方库
import requests
from dotenv import load_dotenv

# 3. 本地模块
from memory import Memory
```

**规则：**
- 标准库导入放在最前面
- 第三方库其次
- 本地模块最后
- 避免使用 `from module import *`
- 模块级别的导入应位于文件顶部

### 类型注解

所有公共方法都应添加类型注解：

```python
def chat(self, user_input: str) -> str:
    ...

def get_messages(self) -> list[dict[str, str]]:
    ...

def add(self, role: str, content: str) -> None:
    ...
```

**规则：**
- 参数和返回值都应有类型注解
- 使用 `list[dict[str, str]]` 而非 `List[Dict[str, str]]`（Python 3.9+）
- 返回 `None` 时也应标注

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `AIChatbot`, `Memory` |
| 函数/方法名 | snake_case | `get_messages`, `set_model` |
| 变量名 | snake_case | `user_input`, `max_messages` |
| 常量 | UPPER_SNAKE_CASE | `API_KEY`, `BASE_URL` |
| 私有方法 | _前缀 | `_load`, `_save_to_file` |
| 布尔变量 | is/has/can 前缀 | `is_connected`, `has_history` |

### 字符串与格式化

- 使用 f-string 进行字符串格式化
- 多行字符串使用三引号

```python
# 推荐
message = f"已切换模型: {model}"
url = f"{self.base_url}/chat/completions"

# 不推荐
message = "已切换模型: " + model
```

### 错误处理

使用具体的异常类型，提供有意义的错误信息：

```python
# 推荐
if not self.api_key or not self.base_url:
    raise ValueError("请在 .env 文件中配置 API_KEY 和 BASE_URL")

try:
    response.raise_for_status()
    return response.json()
except requests.Timeout:
    return "请求超时，请稍后重试"
except requests.RequestException as e:
    return f"网络请求出错: {str(e)}"
```

**规则：**
- 不要使用裸露的 `except:` 或过于宽泛的 `except Exception`
- 异常信息使用中文，与项目风格保持一致
- 在构造函数中进行参数验证

### 文档字符串

为公共类和方法添加文档字符串：

```python
class Memory:
    """管理对话历史的存储与加载。
    
    将对话记录以 Markdown 格式持久化存储，
    支持消息数量限制和历史加载。
    """
    
    def _load(self) -> list[dict[str, str]]:
        """从 markdown 文件加载历史记录。
        
        Returns:
            包含 system 消息和对话历史的消息列表。
        """
```

---

## 项目特定规范

### 用户界面

- 所有用户交互信息使用中文
- 命令行界面简洁明了
- 支持的命令：
  - `history` - 查看对话历史
  - `clear` - 清空对话历史
  - `models` - 列出所有可用模型
  - `models <编号>` - 切换到指定模型（如 `models 1`）
  - `addmodel <id> <name> <desc>` - 添加新模型（如 `addmodel gpt-4o GPT-4o 最新模型`）
  - `delmodel <编号>` - 删除指定模型（如 `delmodel 2`）
  - `exit` - 退出程序

### 模型配置

模型列表通过 `config/models.txt` 文件配置，第一行为表头：

```
id,provider,description
gpt-3.5-turbo,OpenAI,fast and economical
gpt-4,OpenAI,powerful reasoning
qwen-turbo,Alibaba,fast model
```

**格式说明：** `模型ID,供应商,描述（英文）`

如果文件不存在，需使用 `addmodel` 命令添加模型。

### 文件存储

- `chat_history.md` - 对话历史（Markdown 格式）
- `config/models.txt` - 模型列表（CSV 格式，含表头）
- 使用 UTF-8 编码

### API 调用

- 请求超时设置为 30 秒
- 使用 temperature=0.7 作为默认参数
- 错误响应应返回用户友好的中文提示

---

## 文件编辑注意事项

1. 编辑文件前先使用 Read 工具读取文件内容
2. 保留现有代码风格和注释风格
3. 新增功能时遵循现有架构模式
4. 不要添加不必要的注释（代码应自解释）
5. 不要修改 `.env` 文件中的 API 密钥

---

## 常见任务

### 添加新命令

在 `main.py` 的主循环中添加新的条件分支：

```python
elif user_input.startswith("newcommand "):
    arg = user_input[11:].strip()
    print(bot.new_method(arg))
```

### 添加新模型

通过命令行添加（推荐）：
```
addmodel gpt-4o OpenAI latest multimodal model
```

或直接编辑 `config/models.txt` 文件：
```
gpt-4o,OpenAI,latest multimodal model
```

### 删除模型

通过命令行删除：
```
delmodel 2
```

### 添加新的 API 参数

在 `chatbot.py` 的 `chat` 方法中修改请求体：

```python
json={
    "model": self.model,
    "messages": self.memory.get_messages(),
    "temperature": 0.7,
    "new_param": self.new_param  # 新增参数
}
```

### 修改历史记录格式

修改 `memory.py` 中的 `save` 和 `_load` 方法，保持读写格式一致。