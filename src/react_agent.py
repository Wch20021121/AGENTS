"""ReAct推理系统 - Reasoning and Acting"""
import json
import logging
from typing import List, Dict, Any, Optional, Generator
from datetime import datetime


class ReActAgent:
    """ReAct推理Agent"""
    
    def __init__(self, ai_client, tool_registry):
        self.ai_client = ai_client
        self.tool_registry = tool_registry
        self.max_iterations = 10
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """创建系统提示词"""
        tools_desc = self._get_tools_description()
        
        return f"""你是一个智能助手，可以使用工具来完成用户的任务。

请使用ReAct（Reasoning and Acting）格式进行思考和行动：

格式要求：
1. Thought: 你的思考过程，分析当前情况和需要做什么
2. Action: 如果需要使用工具，格式为：Action: tool_name(param1=value1, param2=value2)
3. Observation: 工具执行后的观察结果
4. Final Answer: 当任务完成时给出最终答案

可用工具：
{tools_desc}

重要提示：
- 每次只能执行一个Action
- 如果不需要工具，直接给出Final Answer
- 如果一次工具调用没有完成任务，继续思考和行动
- 最多执行{self.max_iterations}轮思考-行动循环

示例：
Thought: 用户要求我读取文件内容，我需要使用read_file工具
Action: read_file(file_path="example.txt")
Observation: [文件内容]
Thought: 我已经获取了文件内容，现在可以回答用户
Final Answer: 文件内容是..."""
    
    def _get_tools_description(self) -> str:
        """获取工具描述"""
        tools = self.tool_registry.get_all_schemas()
        descriptions = []
        
        for tool in tools:
            func = tool.get("function", {})
            name = func.get("name", "")
            desc = func.get("description", "")
            params = func.get("parameters", {})
            
            # 提取参数说明
            props = params.get("properties", {})
            required = params.get("required", [])
            param_descs = []
            for param_name, param_info in props.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                req_marker = "(必填)" if param_name in required else "(可选)"
                param_descs.append(f"  - {param_name}: {param_type} {req_marker} - {param_desc}")
            
            descriptions.append(f"\n{name}: {desc}")
            if param_descs:
                descriptions.append("参数:")
                descriptions.extend(param_descs)
        
        return "\n".join(descriptions)
    
    def run(self, user_input: str, history: List[Dict] = None) -> Generator[str, None, None]:
        """
        运行ReAct循环
        
        Yields:
            推理过程和结果的字符串片段
        """
        if history is None:
            history = []
        
        # 构建消息
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # 添加历史消息
        for msg in history[-10:]:  # 限制历史消息数量
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        iteration = 0
        final_answer = None
        
        while iteration < self.max_iterations:
            iteration += 1
            logging.info(f"ReAct iteration {iteration}")
            
            # 调用AI获取思考
            full_response = ""
            for chunk in self.ai_client.chat(messages, stream=True):
                full_response += chunk
            
            logging.info(f"AI response: {full_response[:200]}...")
            
            # 解析响应
            parsed = self._parse_response(full_response)
            
            # 如果只有Final Answer，任务完成
            if parsed.get("final_answer") and not parsed.get("action"):
                yield f"\n🤖 {parsed['final_answer']}\n"
                return
            
            # 如果有Action，执行工具
            if parsed.get("action"):
                action_name = parsed["action"]["name"]
                action_params = parsed["action"]["params"]
                
                # 显示思考过程
                if parsed.get("thought"):
                    yield f"\n💭 Thought: {parsed['thought']}\n"
                
                yield f"\n🔧 Action: {action_name}({self._format_params(action_params)})\n"
                
                # 执行工具
                observation = self.tool_registry.execute_tool(action_name, action_params)
                logging.info(f"Tool execution: {action_name}")
                
                # 显示观察结果（截断）
                obs_display = observation[:500] + "..." if len(observation) > 500 else observation
                yield f"\n👁 Observation:\n{obs_display}\n"
                
                # 更新消息历史，添加工具结果
                messages.append({
                    "role": "assistant",
                    "content": full_response
                })
                messages.append({
                    "role": "user",
                    "content": f"Observation: {observation}"
                })
                
                # 检查是否包含Final Answer
                if parsed.get("final_answer"):
                    yield f"\n✅ Final Answer: {parsed['final_answer']}\n"
                    return
            
            else:
                # 没有Action也没有Final Answer，视为直接回答
                yield f"\n🤖 {full_response}\n"
                return
        
        # 达到最大迭代次数
        yield f"\n⚠️ 达到最大迭代次数({self.max_iterations})，请简化您的请求。\n"
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应，提取Thought, Action, Observation, Final Answer"""
        result = {
            "thought": None,
            "action": None,
            "observation": None,
            "final_answer": None
        }
        
        lines = response.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # 检查是否是新章节
            if line.startswith('Thought:') or line.startswith('thought:'):
                if current_section and current_content:
                    self._save_section(result, current_section, '\n'.join(current_content))
                current_section = "thought"
                current_content = [line[8:].strip()]
            
            elif line.startswith('Action:') or line.startswith('action:'):
                if current_section and current_content:
                    self._save_section(result, current_section, '\n'.join(current_content))
                current_section = "action"
                current_content = [line[7:].strip()]
            
            elif line.startswith('Observation:') or line.startswith('observation:'):
                if current_section and current_content:
                    self._save_section(result, current_section, '\n'.join(current_content))
                current_section = "observation"
                current_content = [line[12:].strip()]
            
            elif line.startswith('Final Answer:') or line.startswith('final answer:'):
                if current_section and current_content:
                    self._save_section(result, current_section, '\n'.join(current_content))
                current_section = "final_answer"
                current_content = [line[13:].strip()]
            
            elif current_section:
                current_content.append(line)
        
        # 保存最后一个章节
        if current_section and current_content:
            self._save_section(result, current_section, '\n'.join(current_content))
        
        # 解析Action
        if result["action"]:
            result["action"] = self._parse_action(result["action"])
        
        return result
    
    def _save_section(self, result: Dict, section: str, content: str):
        """保存章节内容"""
        content = content.strip()
        if content:
            result[section] = content
    
    def _parse_action(self, action_str: str) -> Optional[Dict]:
        """解析Action字符串"""
        # 格式: tool_name(param1=value1, param2=value2)
        # 或: tool_name({"param1": "value1", "param2": "value2"})
        
        action_str = action_str.strip()
        if not action_str:
            return None
        
        # 尝试JSON格式
        if action_str.startswith('{') and action_str.endswith('}'):
            try:
                data = json.loads(action_str)
                if "name" in data and "params" in data:
                    return data
            except:
                pass
        
        # 尝试函数调用格式
        import re
        pattern = r'(\w+)\s*\((.*)\)'
        match = re.match(pattern, action_str)
        
        if match:
            tool_name = match.group(1)
            params_str = match.group(2)
            
            # 解析参数
            params = {}
            if params_str.strip():
                # 尝试作为JSON解析
                try:
                    params = json.loads(params_str)
                except:
                    # 手动解析 key=value 格式
                    param_pattern = r'(\w+)\s*=\s*"([^"]*)"'
                    for pm in re.finditer(param_pattern, params_str):
                        params[pm.group(1)] = pm.group(2)
            
            return {
                "name": tool_name,
                "params": params
            }
        
        # 最简单的格式：只有工具名
        if action_str.replace('_', '').isalnum():
            return {
                "name": action_str,
                "params": {}
            }
        
        return None
    
    def _format_params(self, params: Dict) -> str:
        """格式化参数字符串"""
        if not params:
            return ""
        return ", ".join([f"{k}={repr(v)}" for k, v in params.items()])
    
    def chat_with_tools(self, user_input: str, history: List[Dict] = None) -> str:
        """不使用流式输出的聊天方法"""
        result = []
        for chunk in self.run(user_input, history):
            result.append(chunk)
        return "".join(result)


class SimpleReActFormatter:
    """简化版的ReAct格式化器"""
    
    @staticmethod
    def format_thought(thought: str) -> str:
        return f"💭 Thought: {thought}"
    
    @staticmethod
    def format_action(tool_name: str, params: Dict) -> str:
        params_str = ", ".join([f"{k}={repr(v)}" for k, v in params.items()])
        return f"🔧 Action: {tool_name}({params_str})"
    
    @staticmethod
    def format_observation(observation: str) -> str:
        # 截断长文本
        if len(observation) > 300:
            observation = observation[:300] + "\n... (已截断)"
        return f"👁 Observation:\n{observation}"
    
    @staticmethod
    def format_final_answer(answer: str) -> str:
        return f"✅ Final Answer: {answer}"
