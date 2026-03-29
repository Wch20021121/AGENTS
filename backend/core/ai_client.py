"""AI Client - 大模型客户端"""
import requests
import json
from typing import List, Dict, Generator, Optional, Any
import logging

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, messages: List[Dict[str, str]], model: str = "qwen-turbo",
             tools: List[Dict] = None, stream: bool = True) -> Generator[str, None, None]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        try:
            url = f"{self.base_url}/chat/completions"
            logger.info(f"Request to {url}, model: {model}, tools: {len(tools) if tools else 0}")
            
            if stream:
                response = requests.post(url, headers=self.headers, json=payload, stream=True, timeout=120)
                response.raise_for_status()
                
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
                                    
                                    if 'content' in delta and delta['content']:
                                        yield delta['content']
                                    
                                    if choice.get('finish_reason') == 'tool_calls' and tool_calls_buffer:
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
                    
                    if 'tool_calls' in message and message['tool_calls']:
                        tool_calls = message['tool_calls']
                        yield f"\n[TOOL_CALLS]{json.dumps(tool_calls)}[/TOOL_CALLS]\n"
                    
                    if 'content' in message and message['content']:
                        yield message['content']
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            yield f"[错误] 请求失败: {e}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            yield f"[错误] 发生异常: {e}"
    
    def chat_simple(self, messages: List[Dict[str, str]], model: str = "qwen-turbo",
                    tools: List[Dict] = None) -> str:
        result = []
        for chunk in self.chat(messages, model=model, tools=tools, stream=False):
            result.append(chunk)
        return "".join(result)
    
    def test_connection(self) -> bool:
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