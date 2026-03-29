"""Agent Core - 调度层"""
import json
import logging
from typing import Dict, List, Any, Generator, Optional
from ..tools.registry import ToolRegistry
from ..tools.base import ToolResult
from ..config.manager import ConfigManager, SecurityConfig, SystemConfig
from ..storage.session import SessionManager
from ..storage.logger import LoggerManager
from .ai_client import AIClient

logger = logging.getLogger(__name__)

class AgentCore:
    def __init__(self, config_manager: ConfigManager, session_manager: SessionManager,
                 tool_registry: ToolRegistry, logger_manager: LoggerManager):
        self.config_manager = config_manager
        self.session_manager = session_manager
        self.tool_registry = tool_registry
        self.logger_manager = logger_manager
        
        model_config = config_manager.get_model_config()
        self.ai_client = AIClient(model_config.base_url, model_config.api_key)
        self.model_name = model_config.model_name
        
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        tools_desc = self._get_tools_description()
        system_config = self.config_manager.get_system_config()
        
        return f"""你是MiniAgent，一个智能助手，可以使用工具完成用户的任务。

可用工具：
{tools_desc}

重要规则：
1. 分析用户请求，决定是否需要使用工具
2. 如果需要工具，调用对应工具并等待结果
3. 最多执行{system_config.max_iterations}轮工具调用
4. 如果不需要工具，直接回答用户
5. 所有文件操作必须在工作目录范围内
6. 命令执行需要用户开启权限

回复格式：
- 如果使用了工具，说明使用的工具和结果
- 给出清晰、简洁的回答
"""
    
    def _get_tools_description(self) -> str:
        tools = self.tool_registry.get_all_metadata()
        descriptions = []
        
        for tool in tools:
            name = tool["name"]
            desc = tool["description"]
            params = tool["parameters"]
            
            props = params.get("properties", {})
            required = params.get("required", [])
            
            param_list = []
            for param_name, param_info in props.items():
                param_desc = param_info.get("description", "")
                req = "*" if param_name in required else ""
                param_list.append(f"  - {param_name}{req}: {param_desc}")
            
            descriptions.append(f"\n{name}: {desc}")
            if param_list:
                descriptions.extend(param_list)
        
        return "\n".join(descriptions)
    
    def process(self, user_input: str) -> Dict[str, Any]:
        security_config = self.config_manager.get_security_config()
        system_config = self.config_manager.get_system_config()
        work_dir = str(self.config_manager.get_work_dir())
        
        if not self.session_manager.get_current_session_id():
            self.session_manager.create_session()
        
        self.session_manager.add_message("user", user_input)
        
        messages = self._build_messages()
        tools = self.tool_registry.get_all_schemas()
        
        tool_results = []
        final_response = ""
        iterations = 0
        
        while iterations < system_config.max_iterations:
            iterations += 1
            
            response_text = ""
            for chunk in self.ai_client.chat(messages, model=self.model_name, tools=tools, stream=False):
                response_text += chunk
            
            tool_calls = self.ai_client.extract_tool_calls(response_text)
            
            if not tool_calls:
                final_response = response_text.replace("[TOOL_CALLS]", "").replace("[/TOOL_CALLS]", "")
                break
            
            messages.append({"role": "assistant", "content": response_text})
            
            for tc in tool_calls:
                func = tc.get("function", {})
                tool_name = func.get("name", "")
                args_str = func.get("arguments", "{}")
                
                try:
                    params = json.loads(args_str)
                except:
                    params = {}
                
                params["work_dir"] = work_dir
                
                if tool_name == "run_command":
                    params["allow_command"] = security_config.allow_command
                    params["timeout"] = security_config.command_timeout
                    params["dangerous_commands"] = security_config.dangerous_commands
                
                result = self.tool_registry.execute(tool_name, params)
                tool_results.append({
                    "tool": tool_name,
                    "params": params,
                    "result": result.to_dict()
                })
                
                self.logger_manager.log_tool_call(tool_name, params, result.to_dict())
                self.session_manager.add_tool_call(tool_name, params, result.to_dict())
                
                observation = json.dumps(result.to_dict(), ensure_ascii=False)
                messages.append({
                    "role": "user",
                    "content": f"工具 {tool_name} 执行结果: {observation}"
                })
        
        self.session_manager.add_message("assistant", final_response, {"tool_results": tool_results})
        
        return {
            "response": final_response,
            "tool_calls": tool_results,
            "session_id": self.session_manager.get_current_session_id()
        }
    
    def _build_messages(self) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": self.system_prompt}]
        
        history = self.session_manager.get_messages(limit=20)
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            messages.append({"role": role, "content": content})
        
        return messages
    
    def test_connection(self) -> bool:
        return self.ai_client.test_connection()