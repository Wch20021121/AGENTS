import json
from pathlib import Path
from datetime import datetime

class Memory:
    def __init__(self, context_file="chat_history.md", max_messages=20):
        self.context_file = context_file
        self.max_messages = max_messages
        self.messages = self._load()
    
    def _load(self):
        """从 markdown 文件加载历史记录"""
        messages = [{"role": "system", "content": "你是一个 helpful 的助手"}]
        
        if Path(self.context_file).exists():
            with open(self.context_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析 markdown 格式
            import re
            pattern = r'### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\n\*\*User:\*\*\s*(.+?)\n\*\*AI:\*\*\s*(.+?)(?=\n### |\Z)'
            matches = re.findall(pattern, content, re.DOTALL)
            
            for timestamp, user_msg, ai_msg in matches:
                messages.append({"role": "user", "content": user_msg.strip()})
                messages.append({"role": "assistant", "content": ai_msg.strip()})
        
        # 只保留最近的消息
        if len(messages) > self.max_messages + 1:
            messages = [messages[0]] + messages[-self.max_messages:]
        
        return messages
    
    def save(self):
        """保存为 markdown 格式"""
        md_content = "# 对话历史\n\n"
        
        # 跳过 system 消息，只保存 user 和 assistant 的配对
        i = 1
        while i < len(self.messages):
            if self.messages[i]["role"] == "user" and i + 1 < len(self.messages):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_content = self.messages[i]["content"]
                assistant_content = self.messages[i + 1]["content"] if self.messages[i + 1]["role"] == "assistant" else ""
                
                md_content += f"### {timestamp}\n\n"
                md_content += f"**User:** {user_content}\n\n"
                md_content += f"**AI:** {assistant_content}\n\n"
                md_content += "---\n\n"
                i += 2
            else:
                i += 1
        
        with open(self.context_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def add(self, role, content):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages + 1:
            self.messages = [self.messages[0]] + self.messages[-self.max_messages:]
        self.save()
    
    def get_messages(self):
        return self.messages.copy()
    
    def clear(self):
        self.messages = [{"role": "system", "content": "你是一个 helpful 的助手"}]
        Path(self.context_file).unlink(missing_ok=True)
    
    def get_history(self):
        if len(self.messages) <= 1:
            return "暂无对话"
        lines = []
        idx = 1
        for msg in self.messages[1:]:
            role = "你" if msg["role"] == "user" else "AI"
            lines.append(f"[{idx}] {role}: {msg['content'][:50]}{'...' if len(msg['content']) > 50 else ''}")
            if msg["role"] == "assistant":
                idx += 1
        return "\n".join(lines)
