"""MiniAgent - 主入口"""
import sys
import webbrowser
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.api.routes import create_app

def open_browser():
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

def main():
    app = create_app()
    
    print("""
+----------------------------------------------------------+
|      MiniAgent - 本地文件操作智能助手                      |
|                                                          |
|  后端API: http://localhost:5000                          |
|  前端界面: http://localhost:5000 (自动打开)               |
|                                                          |
|  可用接口:                                                |
|    POST /chat       - 发送消息                           |
|    GET  /sessions   - 获取会话列表                       |
|    POST /sessions   - 创建新会话                         |
|    GET  /tools      - 获取工具列表                       |
|    GET  /config     - 获取配置                           |
|    POST /config     - 更新配置                           |
|    GET  /status     - 获取系统状态                       |
+----------------------------------------------------------+
    """)
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()