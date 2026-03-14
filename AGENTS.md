# AGENTS.md

本文件为 AI 编码助手提供项目指南。

## 项目概述

基于 Python 的多用户 AI 对话助手，支持 OpenAI 兼容的 API 交互，对话历史以 Markdown 格式持久化存储。

## 项目结构

```
├── main.py              # 程序入口
├── config/              # 配置包
│   ├── __init__.py      # 包导出
│   ├── settings.py      # 配置管理
│   ├── data.py          # 模型数据类（ModelData）
│   └── logger.py        # 日志系统
├── AI/                  # AI 包
│   ├── __init__.py      # 包导出
│   ├── chatbot.py       # AI 对话逻辑
│   └── memory/          # 记忆子包
│       ├── __init__.py
│       └── memory.py    # 对话历史管理
├── users/               # 用户管理包
│   ├── __init__.py
│   ├── user_manager.py  # 用户管理（Admin, User, UserManager）
│   └── data.py          # 用户数据类（UserData）
├── .env                 # 环境变量
├── log/                 # 日志文件
├── config/models.json   # 模型列表
├── users/admin.json     # 管理员信息
└── users/users.json     # 普通用户信息
```

## 配置说明

### 环境变量（.env）

```ini
# API 配置（管理员使用）
API_KEY=your-api-key
BASE_URL=https://api.openai.com/v1
API_TIMEOUT=30
API_TEMPERATURE=0.7

# 管理员配置
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123456
ADMIN_SECRET_KEY=111111  # 管理员快速登录密钥

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=log
LOG_CONSOLE_OUTPUT=true

# 模型配置
MODELS_PATH=config/models.json

# 对话配置
CHAT_HISTORY_FILE=chat_history.md
MAX_MESSAGES=20
```

### 从配置包导入

```python
from config import (
    API_KEY,
    BASE_URL,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    ADMIN_SECRET_KEY,
    LOG_LEVEL,
    ModelManager,
    get_logger,
)
```

## 代码风格

### 导入规范

```python
# 1. 标准库
import os
from pathlib import Path

# 2. 第三方库
import requests

# 3. 本地包
from config import get_logger, ModelManager
from config.data import ModelData
from AI import AIChatbot
from users import UserManager, Admin, User
from users.data import UserData
```

### 类型注解

所有公共方法需添加类型注解：

```python
def chat(self, user_input: str) -> str:
    ...

def get_messages(self) -> list[dict[str, str]]:
    ...
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `AIChatbot`, `Memory`, `UserManager`, `Admin`, `User` |
| 函数/方法 | snake_case | `get_logger`, `add_model` |
| 常量 | UPPER_SNAKE_CASE | `API_KEY`, `ADMIN_SECRET_KEY` |
| 私有方法 | _前缀 | `_load`, `_save` |

### 文档字符串

为公共类和方法添加文档字符串：

```python
class Memory:
    """对话历史管理器。"""
    
    def add(self, role: str, content: str) -> None:
        """添加消息到对话历史。
        
        Args:
            role: 消息角色。
            content: 消息内容。
        """
```

## 数据类

项目使用数据类（dataclass）来传输数据，每个模块的数据类定义在对应的 `data.py` 文件中。

### users/data.py - UserData

```python
@dataclass
class UserData:
    username: str
    is_admin: bool
    created_at: str
    api_key: Optional[str]
    base_url: Optional[str]
```

**方法**：
- `to_dict()` - 转换为字典（用于 users.json）
- `to_config_dict()` - 转换为 API 配置字典
- `from_dict()` - 从字典创建实例
- `has_personal_api()` - 检查是否配置了个人 API

### config/data.py - ModelData

```python
@dataclass
class ModelData:
    id: str
    provider: str
    description: str
    user: Optional[str]
    is_shared: bool
```

**方法**：
- `to_dict()` - 转换为字典（用于 models.json）
- `from_dict()` - 从字典创建实例
- `display_name()` - 获取显示名称
- `owner_type()` - 获取所有者类型（共享/管理员/用户）
- `can_use()` - 检查用户是否可以使用
- `can_delete()` - 检查用户是否可以删除

## 用户类

### Admin 类（管理员）

**存储位置**: `users/admin.json`

**属性**:
- `username`: 固定为 "admin"
- `created_at`: 创建时间

**登录方式**:
```python
user_mgr.authenticate_admin(secret_key)  # secret_key 来自环境变量 ADMIN_SECRET_KEY
```

**特点**:
- 使用系统 API 配置（环境变量）
- 可以访问所有模型
- 可以管理用户和权限
- 无需个人 API 配置

### User 类（普通用户）

**存储位置**: `users/users.json`

**属性**:
- `username`: 用户名
- `password_hash`: 密码哈希（SHA256）
- `can_use_shared_models`: 是否可以使用共享模型
- `can_use_personal_models`: 是否可以使用个人模型
- `created_at`: 创建时间

**登录方式**:
```python
user_mgr.authenticate(username, password)
```

**特点**:
- 使用个人 API 配置（用于个人模型）
- 权限由管理员分配
- 只能看到自己有权限的模型

## 用户管理

### 创建用户（仅管理员）

```python
result = user_mgr.create_user(
    username="testuser",
    password="testpass123",
    can_use_shared_models=True,
    can_use_personal_models=True,
    operator=admin
)
```

### 设置用户权限（仅管理员）

```python
result = user_mgr.set_user_permissions(
    username="testuser",
    can_use_shared_models=True,   # 允许/禁止共享模型
    can_use_personal_models=False, # 允许/禁止个人模型
    operator=admin
)
```

### 权限检查

```python
# 检查是否可以使用共享模型
if user_mgr.can_use_shared_models():
    # 使用共享模型（系统 API）
    pass

# 检查是否可以使用个人模型
if user_mgr.can_use_personal_models():
    # 使用个人模型（个人 API）
    pass
```

## API 配置

### 系统 API（管理员使用）

- **来源**: `.env` 文件（`API_KEY`, `BASE_URL`）
- **使用场景**: 共享模型
- **配置位置**: 环境变量

### 个人 API（普通用户使用）

- **来源**: `config/users/{username}_config.json`
- **使用场景**: 个人模型
- **配置方式**: `setapi <key> <url>` 命令

```json
{
  "api_key": "user-api-key",
  "base_url": "https://api.example.com/v1"
}
```

## 日志使用

```python
from config import get_logger

logger = get_logger("module_name")

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告")
logger.error("错误")
```

### 日志文件

```
log/
├── main.log        # 主程序
├── chatbot.log     # AI 对话
├── memory.log      # 记忆模块
└── users.log       # 用户管理
```

## 错误处理

```python
try:
    response.raise_for_status()
    return response.json()
except requests.Timeout:
    logger.error("请求超时")
    return "请求超时，请稍后重试"
except requests.RequestException as e:
    logger.error(f"网络错误：{e}")
    return f"网络请求出错：{str(e)}"
```

## 常见任务

### 添加新命令

在 `main.py` 主循环中添加：

```python
elif user_input.startswith("newcmd "):
    arg = user_input[7:].strip()
    logger.debug(f"用户执行新命令：{arg}")
    print(bot.new_method(arg))
```

### 添加新配置项

1. 在 `.env` 中添加：
```ini
NEW_CONFIG=value
```

2. 在 `config/settings.py` 中读取：
```python
NEW_CONFIG = os.getenv("NEW_CONFIG", "default")
```

3. 导出配置（`config/__init__.py`）：
```python
from config.settings import NEW_CONFIG

__all__ = [..., "NEW_CONFIG"]
```

### 修改对话历史格式

修改 `AI/memory/memory.py` 的 `save` 和 `_load` 方法，保持格式一致。

## 测试

```bash
# 运行所有测试
pytest

# 运行单个测试
pytest tests/test_chatbot.py -v
```
