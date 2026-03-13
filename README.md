# AI Chat Assistant

基于 Python 的 AI 对话助手，支持与 OpenAI 兼容的 API 进行交互。

## 功能

- 多模型支持：可切换不同 AI 模型
- 对话历史：自动保存对话记录（Markdown 格式）
- 模型管理：动态添加/删除模型

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量（`.env` 文件）
```
API_KEY=your-api-key
BASE_URL=https://api.openai.com/v1
MODELS_PATH=config/models.txt
```

3. 运行程序
```bash
python main.py
```

## 命令

| 命令 | 说明 |
|------|------|
| `history` | 查看对话历史 |
| `clear` | 清空对话历史 |
| `models` | 列出所有模型 |
| `models <编号>` | 切换模型 |
| `addmodel <id> <provider> <desc>` | 添加模型 |
| `delmodel <编号>` | 删除模型 |
| `exit` | 退出程序 |

## 项目结构

```
├── main.py          # 程序入口
├── chatbot.py       # AI 对话逻辑
├── memory.py        # 对话历史管理
├── config.py        # 配置管理
├── .env             # 环境变量
├── config/
│   └── models.txt   # 模型列表
└── requirements.txt # 依赖列表
```