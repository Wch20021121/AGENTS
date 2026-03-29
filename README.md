# MiniAgent

本地文件操作智能助手 - 前后端分离架构

## 项目结构

```
MiniAgent/
  backend/          # 后端模块
    api/            # API接口层
    core/           # Agent调度层
    tools/          # Tool执行层
    services/       # 服务层
    storage/        # 存储层
    config/         # 配置层
  frontend/         # 前端界面
  config/           # 配置文件
  logs/             # 日志目录
  sessions/         # 会话存储
  run.py            # 主入口
```

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 配置API Key (修改 config/settings.json)
# 启动后端
python run.py

# 打开前端界面
# 访问 frontend/index.html 或 http://localhost:5000
```

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /chat | POST | 发送消息 |
| /sessions | GET/POST | 会话管理 |
| /tools | GET | 工具列表 |
| /config | GET/POST | 配置管理 |
| /status | GET | 系统状态 |

## 命令系统

- `/help` - 显示帮助
- `/skills` - 工具列表
- `/clear` - 清空会话
- `/config` - 查看配置
- `/status` - 系统状态

## 工具

- write_file - 写入文件
- read_file - 读取文件
- search_files - 搜索文件
- delete_file - 删除文件
- run_command - 执行命令