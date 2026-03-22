"""AI客户端模块 - 支持Function Calling"""
import requests
import json
from typing import List, Dict, Generator, Optional, Any
import logging


class AIClient:
    """封装AI API调用"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, messages: List[Dict[str, str]], model: str = None, 
             stream: bool = True, tools: List[Dict] = None) -> Generator[str, None, None]:
        """
        发送聊天请求，支持Function Calling
        
        Args:
            messages: 消息列表，每个消息包含 role 和 content
            model: 模型名称
            stream: 是否使用流式输出
            tools: 工具定义列表（Function Calling格式）
        
        Yields:
            生成的文本片段或函数调用
        """
        if model is None:
            model = "qwen-turbo"  # 默认使用通义千问
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        # 添加工具定义
        if tools:
            payload["tools"] = tools
            # 添加工具选择策略，允许自动选择
            payload["tool_choice"] = "auto"
        
        try:
            url = f"{self.base_url}/chat/completions"
            logging.info(f"Sending request to {url} with model {model}, tools: {len(tools) if tools else 0}")
            
            if stream:
                response = requests.post(url, headers=self.headers, json=payload, stream=True, timeout=120)
                response.raise_for_status()
                
                # 用于累积工具调用
                tool_calls_buffer = []
                current_tool_call = None
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    choice = chunk['choices'][0]
                                    delta = choice.get('delta', {})
                                    
                                    # 检查是否有工具调用
                                    if 'tool_calls' in delta:
                                        tool_calls = delta['tool_calls']
                                        for tc in tool_calls:
                                            tc_id = tc.get('id', '')
                                            tc_function = tc.get('function', {})
                                            
                                            if tc_id:
                                                current_tool_call = {
                                                    'id': tc_id,
                                                    'type': 'function',
                                                    'function': {
                                                        'name': tc_function.get('name', ''),
                                                        'arguments': tc_function.get('arguments', '')
                                                    }
                                                }
                                                tool_calls_buffer.append(current_tool_call)
                                            elif current_tool_call and 'arguments' in tc_function:
                                                current_tool_call['function']['arguments'] += tc_function.get('arguments', '')
                                    
                                    # 常规内容
                                    if 'content' in delta and delta['content']:
                                        yield delta['content']
                                    
                                    # 检查是否完成
                                    if choice.get('finish_reason') == 'tool_calls' and tool_calls_buffer:
                                        # 输出工具调用JSON
                                        yield f"\n[TOOL_CALLS]{json.dumps(tool_calls_buffer)}[/TOOL_CALLS]\n"
                                        tool_calls_buffer = []
                                        current_tool_call = None
                                            
                            except json.JSONDecodeError:
                                continue
            else:
                response = requests.post(url, headers=self.headers, json=payload, timeout=120)
                response.raise_for_status()
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    choice = result['choices'][0]
                    message = choice.get('message', {})
                    
                    # 检查工具调用
                    if 'tool_calls' in message and message['tool_calls']:
                        tool_calls = message['tool_calls']
                        yield f"\n[TOOL_CALLS]{json.dumps(tool_calls)}[/TOOL_CALLS]\n"
                    
                    # 常规内容
                    if 'content' in message and message['content']:
                        yield message['content']
                
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            yield f"[错误] 请求失败: {e}"
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            yield f"[错误] 发生异常: {e}"
    
    def chat_simple(self, messages: List[Dict[str, str]], model: str = None) -> str:
        """非流式简单聊天"""
        result = []
        for chunk in self.chat(messages, model=model, stream=False):
            result.append(chunk)
        return "".join(result)
    
    def summarize_messages(self, messages: List[Dict]) -> str:
        """总结消息列表的核心观点"""
        try:
            # 构建摘要提示
            summary_prompt = """请总结以下对话的核心观点和主题。

要求：
1. 用一句话概括对话的主要内容（摘要）
2. 列出3-5个核心主题/关键词
3. 格式：
   [一句话摘要]
   - 主题1
   - 主题2
   - 主题3

对话内容：
"""
            
            # 提取消息内容
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if content:
                    summary_prompt += f"\n{role.upper()}: {content[:200]}"
            
            summary_messages = [
                {"role": "system", "content": "你是一个对话分析助手，擅长总结核心观点。"},
                {"role": "user", "content": summary_prompt}
            ]
            
            result = self.chat_simple(summary_messages)
            return result.strip()
            
        except Exception as e:
            logging.error(f"Summary generation failed: {e}")
            return f"对话进行中... 消息数: {len(messages)}"
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            messages = [{"role": "user", "content": "Hello"}]
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": "qwen-turbo",
                "messages": messages,
                "stream": False
            }
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def extract_tool_calls(self, text: str) -> List[Dict]:
        """从文本中提取工具调用"""
        import re
        pattern = r'\[TOOL_CALLS\](.*?)\[/TOOL_CALLS\]'
        matches = re.findall(pattern, text, re.DOTALL)
        
        tool_calls = []
        for match in matches:
            try:
                calls = json.loads(match)
                if isinstance(calls, list):
                    tool_calls.extend(calls)
            except:
                pass
        
        return tool_calls
