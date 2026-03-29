"""Command Handler - 命令系统"""
from typing import Dict, Any
from ..config.manager import ConfigManager
from ..storage.session import SessionManager
from ..tools.registry import ToolRegistry
import logging

logger = logging.getLogger(__name__)

class CommandHandler:
    COMMANDS = {
        "/help": "显示帮助信息",
        "/skills": "列出当前注册的tools",
        "/clear": "清空当前聊天记录",
        "/config": "打开或返回当前配置",
        "/status": "查看当前运行状态、模型状态、权限状态"
    }
    
    def __init__(self, config_manager: ConfigManager, session_manager: SessionManager,
                 tool_registry: ToolRegistry, agent_core):
        self.config_manager = config_manager
        self.session_manager = session_manager
        self.tool_registry = tool_registry
        self.agent_core = agent_core
    
    def is_command(self, text: str) -> bool:
        return text.strip().startswith("/")
    
    def handle(self, command: str) -> Dict[str, Any]:
        cmd = command.strip().lower()
        
        if cmd == "/help":
            return self._handle_help()
        elif cmd == "/skills":
            return self._handle_skills()
        elif cmd == "/clear":
            return self._handle_clear()
        elif cmd == "/config":
            return self._handle_config()
        elif cmd == "/status":
            return self._handle_status()
        else:
            return {
                "type": "command_result",
                "command": cmd,
                "success": False,
                "data": None,
                "message": f"未知命令: {cmd}"
            }
    
    def _handle_help(self) -> Dict[str, Any]:
        lines = ["可用命令:\n"]
        for cmd, desc in self.COMMANDS.items():
            lines.append(f"  {cmd:12} - {desc}")
        return {
            "type": "command_result",
            "command": "/help",
            "success": True,
            "data": {"commands": self.COMMANDS},
            "message": "\n".join(lines)
        }
    
    def _handle_skills(self) -> Dict[str, Any]:
        tools = self.tool_registry.get_all_metadata()
        lines = ["当前注册的Tools:\n"]
        for tool in tools:
            name = tool["name"]
            desc = tool["description"]
            perm = tool["permission_type"]
            lines.append(f"  - {name}: {desc} (权限: {perm})")
        return {
            "type": "command_result",
            "command": "/skills",
            "success": True,
            "data": {"tools": tools},
            "message": "\n".join(lines)
        }
    
    def _handle_clear(self) -> Dict[str, Any]:
        self.session_manager.clear_current_session()
        return {
            "type": "command_result",
            "command": "/clear",
            "success": True,
            "data": None,
            "message": "已清空当前会话记录"
        }
    
    def _handle_config(self) -> Dict[str, Any]:
        config = self.config_manager.get_all()
        model = self.config_manager.get_model_config()
        security = self.config_manager.get_security_config()
        system = self.config_manager.get_system_config()
        
        lines = ["当前配置:\n"]
        lines.append(f"模型: {model.model_name} @ {model.base_url}")
        lines.append(f"命令执行: {'开启' if security.allow_command else '关闭'}")
        lines.append(f"工作目录: {system.work_dir}")
        
        return {
            "type": "command_result",
            "command": "/config",
            "success": True,
            "data": config,
            "message": "\n".join(lines)
        }
    
    def _handle_status(self) -> Dict[str, Any]:
        model_ok = self.agent_core.test_connection()
        security = self.config_manager.get_security_config()
        session_id = self.session_manager.get_current_session_id()
        
        lines = ["系统状态:\n"]
        lines.append(f"模型连接: {'正常' if model_ok else '异常'}")
        lines.append(f"命令权限: {'开启' if security.allow_command else '关闭'}")
        lines.append(f"当前会话: {session_id or '无'}")
        lines.append(f"注册工具: {len(self.tool_registry.list_tools())}")
        
        return {
            "type": "command_result",
            "command": "/status",
            "success": True,
            "data": {
                "model_connected": model_ok,
                "command_allowed": security.allow_command,
                "session_id": session_id,
                "tools_count": len(self.tool_registry.list_tools())
            },
            "message": "\n".join(lines)
        }