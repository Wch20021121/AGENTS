# AI Chat Assistant

基于 Python 的多用户 AI 对话助手，支持 OpenAI 兼容 API。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```ini
# API 配置（管理员使用）
API_KEY=your-api-key
BASE_URL=https://api.openai.com/v1

# 管理员配置
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123456
ADMIN_SECRET_KEY=111111  # 管理员快速登录密钥
```

### 3. 运行

```bash
python main.py
```

### 4. 登录

**管理员快速登录：**
```
admin 111111
```

**普通用户登录：**
```
login
用户名：testuser
密码：testpass123
```

## 命令

### 登录

| 命令 | 说明 |
|------|------|
| `admin <密钥>` | 管理员快速登录（密钥：111111） |
| `login` | 普通用户登录 |
| `logout` | 登出 |

### 用户管理（仅管理员）

| 命令 | 说明 |
|------|------|
| `users` | 列出所有用户 |
| `adduser <名> <密>` | 创建用户 |
| `deluser <名>` | 删除用户 |
| `setperm <名> <shared|personal> <on|off>` | 设置用户权限 |

**权限说明：**
- `shared`：使用共享模型的权限
- `personal`：使用个人模型的权限

**示例：**
```
setperm testuser shared on     # 允许使用共享模型
setperm testuser personal off  # 禁止个人模型
```

### 对话

| 命令 | 说明 |
|------|------|
| `history` | 查看对话历史 |
| `clear` | 清空对话历史 |
| `[直接输入]` | 与 AI 对话 |

### 模型管理

| 命令 | 说明 | 权限 |
|------|------|------|
| `models` | 列出模型 | 已登录用户 |
| `models <编号>` | 切换模型 | 已登录用户 |
| `addmodel <id> <名> <desc>` | 添加个人模型 | 已登录用户 |
| `addmodel <id> <名> <desc> --shared` | 添加共享模型 | 管理员 |
| `delmodel <编号>` | 删除模型 | 模型所有者/管理员 |

### API 配置

| 命令 | 说明 | 备注 |
|------|------|------|
| `setapi <key> <url>` | 设置个人 API | 仅普通用户需要 |
| `getapi` | 查看 API 配置 | 管理员显示系统 API |

**说明：**
- 管理员使用系统 API（环境变量配置），无需设置个人 API
- 普通用户使用个人模型时需要设置个人 API
- 共享模型使用系统 API，无需个人配置

## 项目结构

```
├── main.py              # 程序入口
├── config/              # 配置包
│   ├── settings.py      # 配置管理
│   ├── data.py          # 模型数据类
│   └── logger.py        # 日志系统
├── AI/                  # AI 包
│   ├── chatbot.py       # 对话逻辑
│   └── memory/          # 记忆模块
├── users/               # 用户管理包
│   ├── user_manager.py  # 用户管理
│   └── data.py          # 用户数据类
├── log/                 # 日志文件
├── config/models.json   # 模型列表
├── users/admin.json     # 管理员信息
└── users/users.json     # 普通用户信息
```

## 用户权限系统

### 管理员
- 使用 `admin <密钥>` 快速登录（密钥：111111）
- 使用系统 API 配置（环境变量）
- 可以访问所有模型（共享 + 个人）
- 可以创建/删除用户
- 可以设置用户权限
- 可以添加共享模型

### 普通用户
- 使用 `login` 命令登录
- 可以被管理员赋予以下权限：
  - 使用共享模型（无需个人 API）
  - 使用个人模型（需要设置个人 API）
- 只能看到自己有权限的模型
- 可以添加自己的个人模型

## 模型配置

模型文件使用 JSON 格式 (`config/models.json`)：

```json
{
  "id": "qwen3.5-plus",
  "provider": "qwen3.5-plus",
  "description": "文本生成、深度思考、视觉理解",
  "user": "admin",
  "is_shared": true
}
```

字段说明：
- `id`: 模型 ID
- `provider`: 提供商名称
- `description`: 模型描述
- `user`: 模型所有者
- `is_shared`: 是否共享

模型可见性：
- `is_shared=true`: 共享模型，所有有权限的用户可见
- `is_shared=false` 且 `user=admin`: 管理员模型，仅管理员可见
- `is_shared=false` 且 `user={用户名}`: 个人模型，仅该用户可见

## 数据存储

- **管理员信息**: `users/admin.json`
- **普通用户信息**: `users/users.json`
- **用户 API 配置**: `config/users/{username}_config.json`
- **对话历史**: `AI/memory/data/{username}/chat_history.md`

## 日志

日志文件位于 `log/` 目录：
- `main.log` - 主程序日志
- `chatbot.log` - 对话模块日志
- `memory.log` - 记忆模块日志
- `users.log` - 用户管理日志
