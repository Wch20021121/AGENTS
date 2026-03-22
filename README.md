# 多轮对话AI系统

这是一个支持多轮对话的AI系统，允许用户配置API、管理对话历史。

## 快速开始

1. 配置API:
   编辑 `config/api_config.json` 添加你的API配置

2. 运行程序:
   ```bash
   python src/main.py
   ```

## 命令说明

- `/sessions` - 列出所有历史会话
- `/load <ID>` - 加载指定会话
- `/new` - 创建新会话
- `/config` - 查看和修改配置
- `/help` - 显示帮助
- `/quit` - 退出程序

## 目录结构

```
├── config/          # 配置文件
├── sessions/        # 对话历史
├── logs/           # 日志文件
├── src/            # 源代码
└── 对话记录.md      # 对话记录追踪
```

## 配置说明

### API配置 (config/api_config.json)

```json
{
  "default": "provider_name",
  "providers": {
    "provider_name": {
      "base_url": "https://api.example.com/v1",
      "api_key": "your-api-key"
    }
  }
}
```

## 日志

日志文件保存在 `logs/app.log`，包含所有运行日志。
