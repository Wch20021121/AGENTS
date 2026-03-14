"""
程序入口 - AI 对话助手主程序。

提供命令行交互界面，
支持对话、历史管理、模型管理、用户管理等功能。
"""
import sys

# 设置 UTF-8 编码输出（仅在 Windows 下）
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

from config import get_logger, LoggerConfig, ModelManager
from AI import AIChatbot
from users import UserManager
from users.user_manager import Admin, User

logger = get_logger("main")


def main():
    """主函数 - 处理用户交互循环。"""
    LoggerConfig.init()
    logger.info("AI 对话助手启动")
    
    user_mgr = UserManager()
    bot = None
    
    print("=== AI 对话助手 ===")
    print("\n登录方式：")
    print("  1. 管理员快速登录：输入 'admin <密钥>'（密钥：111111）")
    print("  2. 普通用户登录：输入 'login'，然后输入用户名和密码")
    print("\n命令：help 查看所有命令\n")
    
    while True:
        try:
            if not bot or not user_mgr.current_user:
                prompt = "未登录> "
            elif isinstance(user_mgr.current_user, Admin):
                prompt = "管理员> "
            else:
                prompt = f"{user_mgr.current_user.username}> "
            
            user_input = input(prompt).strip()
            
            if user_input == "exit":
                logger.info("用户退出程序")
                print("再见！")
                break
            
            elif user_input == "help":
                print_help(user_mgr.current_user)
            
            # 管理员快速登录：admin <密钥>
            elif user_input.startswith("admin "):
                secret_key = user_input[6:].strip()
                
                if user_mgr.authenticate_admin(secret_key):
                    if user_mgr.current_user is None:
                        print("登录失败：无法获取管理员信息")
                        continue
                    logger.info("管理员使用密钥登录成功")
                    # 直接传递 Admin 对象
                    bot = AIChatbot(user=user_mgr.current_user, user_mgr=user_mgr)
                    print("\n欢迎，管理员！")
                    print(f"{bot.model_manager.get_model_info()}\n")
                else:
                    print("登录失败：管理员密钥错误")
            
            elif user_input == "login":
                username = input("用户名：").strip()
                password = input("密码：").strip()
                
                if user_mgr.authenticate(username, password):
                    if user_mgr.current_user is None:
                        print("登录失败：无法获取用户信息")
                        continue
                    logger.info(f"用户 {username} 登录成功")
                    # 直接传递 User 对象
                    bot = AIChatbot(user=user_mgr.current_user, user_mgr=user_mgr)
                    print(f"\n欢迎，{username}！")
                    print(f"{bot.model_manager.get_model_info()}\n")
                else:
                    print("登录失败：用户名或密码错误")
            
            elif user_input == "logout":
                if user_mgr.current_user:
                    user_mgr.logout()
                    bot = None
                    print("已登出")
                else:
                    print("当前未登录")
            
            elif user_input == "users":
                if not user_mgr.current_user:
                    print("请先登录")
                    continue
                print(user_mgr.list_users())
            
            elif user_input.startswith("adduser "):
                if not user_mgr.current_user:
                    print("请先登录")
                    continue
                
                if not isinstance(user_mgr.current_user, Admin):
                    print("错误：只有管理员可以创建用户")
                    continue
                
                parts = user_input[8:].strip().split(maxsplit=1)
                if len(parts) != 2:
                    print("用法：adduser <用户名> <密码>")
                    continue
                
                username, password = parts
                result = user_mgr.create_user(username, password, operator=user_mgr.current_user)
                print(result)
            
            elif user_input.startswith("deluser "):
                if not user_mgr.current_user:
                    print("请先登录")
                    continue
                
                if not isinstance(user_mgr.current_user, Admin):
                    print("错误：只有管理员可以删除用户")
                    continue
                
                username = user_input[8:].strip()
                result = user_mgr.delete_user(username, operator=user_mgr.current_user)
                print(result)
            
            elif user_input.startswith("setperm "):
                if not user_mgr.current_user:
                    print("请先登录")
                    continue
                
                if not isinstance(user_mgr.current_user, Admin):
                    print("错误：只有管理员可以设置用户权限")
                    continue
                
                parts = user_input[8:].strip().split()
                if len(parts) < 2:
                    print("用法：setperm <用户名> <shared|personal> <on|off>")
                    print("  示例：setperm user1 shared on    # 允许使用共享模型")
                    print("  示例：setperm user1 personal off # 禁止使用个人模型")
                    continue
                
                username = parts[0]
                perm_type = parts[1]
                value = parts[2] if len(parts) > 2 else "on"
                
                can_use_shared = None
                can_use_personal = None
                
                if perm_type == "shared":
                    can_use_shared = (value.lower() == "on")
                elif perm_type == "personal":
                    can_use_personal = (value.lower() == "on")
                else:
                    print("错误：权限类型必须是 'shared' 或 'personal'")
                    continue
                
                result = user_mgr.set_user_permissions(
                    username,
                    can_use_shared_models=can_use_shared,
                    can_use_personal_models=can_use_personal,
                    operator=user_mgr.current_user
                )
                print(result)
            
            elif not bot or not user_mgr.current_user:
                print("请先登录（使用 admin <密钥> 或 login 命令）")
            
            elif user_input == "history":
                logger.debug(f"用户 {user_mgr.current_user.username if hasattr(user_mgr.current_user, 'username') else 'admin'} 查看历史")
                print(bot.memory.get_history())
            
            elif user_input == "clear":
                logger.info(f"用户 {user_mgr.current_user.username if hasattr(user_mgr.current_user, 'username') else 'admin'} 清空历史")
                bot.memory.clear()
                print("已清空历史")
            
            elif user_input == "models":
                logger.debug(f"用户 {user_mgr.current_user.username if hasattr(user_mgr.current_user, 'username') else 'admin'} 查看模型列表")
                print(bot.model_manager.list_models())
            
            elif user_input.startswith("models "):
                try:
                    index = int(user_input[7:].strip())
                    result = bot.model_manager.set_model(index)
                    logger.info(f"用户 {user_mgr.current_user.username if hasattr(user_mgr.current_user, 'username') else 'admin'} 切换模型：{result}")
                    print(result)
                except ValueError:
                    logger.warning("无效的模型编号")
                    print("请输入有效的数字编号")
            
            elif user_input.startswith("addmodel "):
                parts = user_input[9:].strip().split(maxsplit=2)
                if len(parts) >= 2:
                    model_id = parts[0]
                    name = parts[1]
                    desc = parts[2] if len(parts) > 2 else ""
                    
                    shared = "--shared" in user_input
                    if shared and not isinstance(user_mgr.current_user, Admin):
                        print("错误：只有管理员可以添加共享模型")
                        continue
                    
                    result = bot.model_manager.add_model(model_id, name, desc, shared=shared)
                    logger.info(f"用户 {user_mgr.current_user.username if hasattr(user_mgr.current_user, 'username') else 'admin'} 添加模型：{result}")
                    print(result)
                else:
                    print("用法：addmodel <模型 ID> <名称> [描述] [--shared]")
            
            elif user_input.startswith("delmodel "):
                try:
                    index = int(user_input[9:].strip())
                    result = bot.model_manager.remove_model(index, operator=user_mgr.current_user)
                    logger.info(f"用户 {user_mgr.current_user.username if hasattr(user_mgr.current_user, 'username') else 'admin'} 删除模型：{result}")
                    print(result)
                except ValueError:
                    logger.warning("无效的模型编号")
                    print("请输入有效的数字编号")
            
            elif user_input.startswith("setapi "):
                if not user_mgr.current_user:
                    print("请先登录")
                    continue
                
                # 管理员不需要设置个人 API
                if isinstance(user_mgr.current_user, Admin):
                    print("管理员使用系统 API 配置，无需设置个人 API")
                    continue
                
                parts = user_input[5:].strip().split(maxsplit=1)
                if len(parts) != 2:
                    print("用法：setapi <api_key> <base_url>")
                    continue
                
                api_key, base_url = parts
                result = user_mgr.set_user_config(api_key, base_url)
                print(result)
                
                # 重新初始化聊天机器人（使用更新后的配置）
                if user_mgr.current_user:
                    bot = AIChatbot(user=user_mgr.current_user, user_mgr=user_mgr)
            
            elif user_input == "getapi":
                if not user_mgr.current_user:
                    print("请先登录")
                    continue
                
                # 管理员显示系统 API
                if isinstance(user_mgr.current_user, Admin):
                    from config import API_KEY, BASE_URL
                    key_preview = API_KEY[:8] + "..." if len(API_KEY) > 8 else API_KEY
                    print("系统 API 配置（用于共享模型）：")
                    print(f"  API Key: {key_preview}")
                    print(f"  Base URL: {BASE_URL}")
                    continue
                
                config = user_mgr.get_user_config()
                if config.get("api_key"):
                    key_preview = config["api_key"][:8] + "..." if len(config["api_key"]) > 8 else config["api_key"]
                    print(f"个人 API 配置：")
                    print(f"  API Key: {key_preview}")
                    print(f"  Base URL: {config['base_url']}")
                else:
                    print("未配置个人 API，请使用 setapi 命令设置")
            
            else:
                username = user_mgr.current_user.username if hasattr(user_mgr.current_user, 'username') else 'admin'
                logger.debug(f"用户 {username} 发送消息：{user_input[:30]}...")
                response = bot.chat(user_input)
                print(f"AI: {response}\n")
        
        except KeyboardInterrupt:
            logger.info("用户中断程序")
            print("\n再见！")
            break
        except Exception as e:
            logger.error(f"未处理的异常：{e}")
            print(f"发生错误：{e}")
            break
    
    logger.info("程序退出")


def print_help(user):
    """打印帮助信息。
    
    Args:
        user: 当前用户。
    """
    print("\n=== 命令帮助 ===")
    print("\n登录：")
    print("  admin <密钥>   - 管理员快速登录（密钥：111111）")
    print("  login          - 普通用户登录")
    print("  logout         - 登出")
    
    print("\n用户管理（仅管理员）：")
    print("  users          - 列出所有用户")
    print("  adduser <名> <密> - 创建用户")
    print("  deluser <名>   - 删除用户")
    print("  setperm <名> <shared|personal> <on|off> - 设置用户权限")
    
    print("\n对话：")
    print("  history        - 查看对话历史")
    print("  clear          - 清空对话历史")
    print("  [直接输入]     - 与 AI 对话")
    
    print("\n模型管理：")
    print("  models         - 列出模型")
    print("  models <编号>  - 切换模型")
    print("  addmodel <id> <名> [desc] [--shared] - 添加模型")
    print("  delmodel <编号> - 删除模型")
    
    print("\nAPI 配置：")
    print("  setapi <key> <url> - 设置个人 API（普通用户用于个人模型）")
    print("  getapi         - 查看 API 配置")
    print("  注：管理员使用系统 API，无需设置个人 API")
    
    print("\n其他：")
    print("  help           - 显示帮助")
    print("  exit           - 退出程序\n")


if __name__ == "__main__":
    main()
