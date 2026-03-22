"""主程序入口 - ReAct模式"""
import sys
import logging
from pathlib import Path

# 添加src和tools到路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigManager
from session_manager import SessionManager
from ai_client import AIClient
from commands import CommandHandler
from react_agent import ReActAgent
from tools import create_tool_registry


def setup_logging(log_file: str = "logs/app.log"):
    """配置日志"""
    Path(log_file).parent.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def print_banner():
    """打印欢迎信息"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║      🤖 多轮对话AI系统 - ReAct模式                        ║
║                                                          ║
║  可用命令:                                                ║
║    /sessions  - 列出历史会话（含AI摘要）                  ║
║    /load <ID> - 加载指定会话                             ║
║    /new       - 创建新会话                               ║
║    /config    - 配置管理                                 ║
║    /help      - 帮助                                     ║
║    /quit      - 退出                                     ║
║                                                          ║
║  工具功能:                                                ║
║    • write_file    - 写入文件                            ║
║    • read_file     - 读取文件                            ║
║    • delete_file   - 删除文件                            ║
║    • list_files    - 列出文件                            ║
║    • execute_command - 执行命令                          ║
║    • search_files  - 搜索文件                            ║
║                                                          ║
║  系统采用ReAct格式: Thought → Action → Observation       ║
╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_react_example():
    """打印ReAct示例"""
    example = """
💡 ReAct交互示例:

你: 帮我读取config/settings.json文件

💭 Thought: 用户想要读取配置文件，我需要使用read_file工具
🔧 Action: read_file(file_path="config/settings.json")
👁 Observation: 📄 文件: .../config/settings.json
   总行数: 5 | 显示: 第1-5行
   ...

✅ Final Answer: 配置文件内容如下：
   {
     "log_level": "INFO",
     ...
   }

"""
    print(example)


def main():
    """主函数"""
    setup_logging()
    logging.info("程序启动 - ReAct模式")
    
    # 初始化组件
    config_manager = ConfigManager()
    settings = config_manager.load_settings()
    
    session_manager = SessionManager(settings.get("session_dir", "sessions"))
    command_handler = CommandHandler(config_manager, session_manager)
    
    # 初始化工具注册表
    tool_registry = create_tool_registry()
    logging.info(f"加载了 {len(tool_registry.list_tools())} 个工具")
    
    # 获取API配置
    provider = config_manager.get_current_provider()
    if not provider:
        print("❌ 错误: 未配置API，请先配置config/api_config.json")
        logging.error("API not configured")
        return
    
    # 初始化AI客户端
    ai_client = AIClient(provider["base_url"], provider["api_key"])
    
    # 测试连接
    if not ai_client.test_connection():
        print("⚠️ 警告: API连接测试失败，请检查配置")
    
    # 设置会话摘要回调
    def summary_callback(messages):
        return ai_client.summarize_messages(messages)
    
    session_manager.set_summary_callback(summary_callback)
    
    # 初始化ReAct Agent
    react_agent = ReActAgent(ai_client, tool_registry)
    
    print_banner()
    print_react_example()
    
    logging.info(f"使用API: {config_manager.load_api_config().get('default')}")
    
    # 创建新会话或加载已有会话
    session_id = session_manager.create_session()
    print(f"✅ 已创建新会话: {session_id}\n")
    logging.info(f"Created session: {session_id}")
    
    # 主循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n🧑 你: ").strip()
            
            if not user_input:
                continue
            
            logging.info(f"User input: {user_input[:50]}...")
            
            # 检查是否为命令
            if command_handler.is_command(user_input):
                result = command_handler.handle(user_input)
                
                # 如果是sessions命令，显示增强的列表
                if user_input.startswith("/sessions"):
                    sessions = session_manager.list_sessions()
                    print(f"\n{session_manager.format_sessions_for_display(sessions)}")
                    logging.info(f"Displayed {len(sessions)} sessions")
                else:
                    print(f"\n{result['result']}")
                
                logging.info(f"Command result: {result.get('action', 'handled')}")
                
                if result.get("action") == "quit":
                    # 生成最终摘要
                    session_manager.generate_final_summary()
                    break
                continue
            
            # 保存用户消息
            session_manager.add_message("user", user_input)
            
            # 准备历史消息
            messages = session_manager.get_formatted_history()
            
            # 使用ReAct Agent处理
            print("\n🤖 AI (ReAct模式):")
            ai_response = ""
            
            try:
                for chunk in react_agent.run(user_input, messages):
                    print(chunk, end="", flush=True)
                    ai_response += chunk
            except Exception as e:
                error_msg = f"[ReAct执行出错: {e}]"
                print(error_msg)
                logging.error(f"ReAct error: {e}")
                ai_response = error_msg
            
            print()  # 换行
            
            # 保存AI回复（去除ReAct过程，只保留最终答案）
            if ai_response:
                # 提取Final Answer部分
                import re
                final_match = re.search(r'Final Answer:(.+?)$', ai_response, re.DOTALL)
                if final_match:
                    final_answer = final_match.group(1).strip()
                else:
                    # 如果没有Final Answer标记，保存完整响应
                    final_answer = ai_response
                
                session_manager.add_message("assistant", final_answer)
                logging.info(f"AI response saved, length: {len(final_answer)}")
        
        except KeyboardInterrupt:
            print("\n\n再见！")
            session_manager.generate_final_summary()
            logging.info("Program interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            logging.error(f"Unexpected error: {e}", exc_info=True)
    
    logging.info("程序结束")


if __name__ == "__main__":
    main()
