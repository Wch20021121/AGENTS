"""命令处理模块"""
from typing import List, Dict
import logging


class CommandHandler:
    """处理用户命令"""
    
    COMMANDS = {
        "/sessions": "列出所有历史会话",
        "/load": "加载指定会话，用法: /load <会话ID>",
        "/new": "创建新会话",
        "/config": "查看和修改配置",
        "/help": "显示帮助信息",
        "/quit": "退出程序",
    }
    
    def __init__(self, config_manager, session_manager):
        self.config_manager = config_manager
        self.session_manager = session_manager
    
    def handle(self, command_line: str) -> Dict:
        """
        处理命令
        
        Returns:
            Dict 包含:
            - handled: bool 是否已处理
            - result: str 处理结果
            - action: str 特殊动作 (如 'quit')
        """
        parts = command_line.strip().split(maxsplit=1)
        if not parts:
            return {"handled": False, "result": ""}
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == "/sessions":
            return self._handle_sessions()
        elif cmd == "/load":
            return self._handle_load(args)
        elif cmd == "/new":
            return self._handle_new()
        elif cmd == "/config":
            return self._handle_config(args)
        elif cmd == "/help":
            return self._handle_help()
        elif cmd in ["/quit", "/exit", "/q"]:
            return self._handle_quit()
        else:
            return {
                "handled": False,
                "result": f"未知命令: {cmd}\n输入 /help 查看可用命令"
            }
    
    def _handle_sessions(self) -> Dict:
        """处理 /sessions 命令"""
        sessions = self.session_manager.list_sessions()
        if not sessions:
            return {"handled": True, "result": "暂无历史会话"}
        
        lines = ["📚 历史会话列表:", ""]
        for i, session in enumerate(sessions, 1):
            lines.append(f"{i}. {session['id']}")
            lines.append(f"   修改时间: {session['modified']}")
            lines.append(f"   文件大小: {session['size']} bytes")
            lines.append("")
        
        lines.append("使用 /load <会话ID> 加载指定会话")
        return {"handled": True, "result": "\n".join(lines)}
    
    def _handle_load(self, session_id: str) -> Dict:
        """处理 /load 命令"""
        if not session_id:
            return {"handled": True, "result": "用法: /load <会话ID>\n使用 /sessions 查看可用会话"}
        
        session = self.session_manager.load_session(session_id)
        if session:
            msg_count = len(session.get("messages", []))
            return {
                "handled": True,
                "result": f"✅ 已加载会话: {session['id']}\n共 {msg_count} 条消息"
            }
        else:
            return {
                "handled": True,
                "result": f"❌ 未找到会话: {session_id}\n使用 /sessions 查看可用会话"
            }
    
    def _handle_new(self) -> Dict:
        """处理 /new 命令"""
        session_id = self.session_manager.create_session()
        return {"handled": True, "result": f"✅ 已创建新会话: {session_id}"}
    
    def _handle_config(self, args: str) -> Dict:
        """处理 /config 命令"""
        if not args:
            # 显示当前配置
            config = self.config_manager.load_api_config()
            current = config.get("default", "未设置")
            providers = list(config.get("providers", {}).keys())
            
            lines = [
                "⚙️ 当前配置:",
                f"当前提供商: {current}",
                f"可用提供商: {', '.join(providers)}",
                "",
                "修改配置:",
                "  /config provider <名称>  - 切换提供商",
            ]
            return {"handled": True, "result": "\n".join(lines)}
        
        # 解析配置命令
        parts = args.split(maxsplit=1)
        if len(parts) >= 2 and parts[0] == "provider":
            provider_name = parts[1]
            if self.config_manager.set_provider(provider_name):
                return {"handled": True, "result": f"✅ 已切换到提供商: {provider_name}"}
            else:
                return {"handled": True, "result": f"❌ 未知的提供商: {provider_name}"}
        
        return {"handled": True, "result": "用法: /config provider <名称>"}
    
    def _handle_help(self) -> Dict:
        """处理 /help 命令"""
        lines = ["🤖 可用命令:", ""]
        for cmd, desc in self.COMMANDS.items():
            lines.append(f"  {cmd:12} - {desc}")
        lines.append("")
        lines.append("直接输入文字即可与AI对话")
        return {"handled": True, "result": "\n".join(lines)}
    
    def _handle_quit(self) -> Dict:
        """处理 /quit 命令"""
        return {"handled": True, "result": "再见！", "action": "quit"}
    
    def is_command(self, text: str) -> bool:
        """检查是否为命令"""
        return text.strip().startswith("/")
