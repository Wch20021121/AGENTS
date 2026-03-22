"""会话管理模块 - 支持AI总结核心观点"""
import json
import os
from pathlib import Path
from datetime import datetime
import re
from typing import List, Dict, Optional, Callable


class SessionManager:
    """管理对话会话和历史记录"""
    
    def __init__(self, session_dir="sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.current_session = None
        self.current_file = None
        self.summary_callback = None  # AI总结回调函数
    
    def set_summary_callback(self, callback: Callable[[List[Dict]], str]):
        """设置AI总结回调函数"""
        self.summary_callback = callback
    
    def create_session(self):
        """创建新会话"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.current_session = {
            "id": timestamp,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "summary": "新会话 - 等待生成摘要",
            "core_topics": [],
            "message_count": 0,
            "messages": []
        }
        self.current_file = self.session_dir / f"{timestamp}.md"
        self._save_session()
        return self.current_session["id"]
    
    def add_message(self, role: str, content: str):
        """添加消息到当前会话"""
        if self.current_session is None:
            self.create_session()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.current_session["messages"].append(message)
        self.current_session["message_count"] = len(self.current_session["messages"])
        self.current_session["updated_at"] = datetime.now().isoformat()
        
        # 每5条消息更新一次摘要
        if self.current_session["message_count"] % 5 == 0 and self.summary_callback:
            self._update_summary()
        
        self._save_session()
    
    def _update_summary(self):
        """更新会话摘要"""
        if not self.summary_callback or not self.current_session:
            return
        
        try:
            messages = self.current_session["messages"]
            summary_result = self.summary_callback(messages)
            
            # 解析AI返回的摘要
            lines = summary_result.split('\n')
            summary = lines[0] if lines else "对话进行中..."
            
            # 提取核心主题
            core_topics = []
            for line in lines[1:]:
                if line.startswith('- ') or line.startswith('• '):
                    core_topics.append(line[2:].strip())
            
            self.current_session["summary"] = summary
            self.current_session["core_topics"] = core_topics
        except Exception as e:
            self.current_session["summary"] = f"摘要生成失败: {e}"
    
    def generate_final_summary(self):
        """生成最终摘要"""
        if not self.summary_callback or not self.current_session:
            return
        
        try:
            messages = self.current_session["messages"]
            summary_result = self.summary_callback(messages)
            
            lines = summary_result.split('\n')
            self.current_session["summary"] = lines[0] if lines else "对话摘要"
            
            core_topics = []
            for line in lines[1:]:
                if line.startswith('- ') or line.startswith('• ') or line.startswith('* '):
                    core_topics.append(line[2:].strip())
            self.current_session["core_topics"] = core_topics
            
            self._save_session()
        except Exception as e:
            pass
    
    def _save_session(self):
        """保存会话到文件"""
        if self.current_session is None or self.current_file is None:
            return
        
        content = self._format_session_to_markdown()
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _format_session_to_markdown(self):
        """将会话格式化为Markdown"""
        session = self.current_session
        
        lines = [
            f"# 对话会话 {session['id']}",
            f"",
            f"**创建时间**: {session['created_at']}",
            f"**更新时间**: {session['updated_at']}",
            f"**消息数量**: {session['message_count']}",
            f"",
            f"## 📋 会话摘要",
            f"",
            f"{session.get('summary', '暂无摘要')}",
            f"",
        ]
        
        # 核心主题
        core_topics = session.get('core_topics', [])
        if core_topics:
            lines.extend([
                f"### 🔑 核心主题",
                f"",
            ])
            for topic in core_topics:
                lines.append(f"- {topic}")
            lines.append("")
        
        lines.extend([
            f"---",
            f"",
            f"## 💬 对话记录",
            f"",
        ])
        
        for msg in session["messages"]:
            role_display = "🧑" if msg["role"] == "user" else "🤖"
            lines.extend([
                f"### {role_display} {msg['role'].upper()} [{msg['timestamp']}]",
                f"",
                f"{msg['content']}",
                f"",
                f"---",
                f"",
            ])
        
        return "\n".join(lines)
    
    def list_sessions(self):
        """列出所有会话 - 包含摘要信息"""
        sessions = []
        for file in self.session_dir.glob("*.md"):
            session_data = self._parse_session_info(file)
            if session_data:
                sessions.append(session_data)
        
        # 按时间倒序排列
        sessions.sort(key=lambda x: x["id"], reverse=True)
        return sessions
    
    def _parse_session_info(self, file_path: Path) -> Optional[Dict]:
        """解析会话基本信息"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            session_id = file_path.stem
            stat = file_path.stat()
            
            # 提取摘要
            summary = "未解析到摘要"
            core_topics = []
            message_count = 0
            
            # 使用正则提取摘要
            import re
            
            # 提取消息数量
            msg_match = re.search(r'\*\*消息数量\*\*:\s*(\d+)', content)
            if msg_match:
                message_count = int(msg_match.group(1))
            
            # 提取摘要
            summary_match = re.search(r'## 📋 会话摘要\s*\n\s*\n(.+?)(?=\n\s*###|\n\s*---|\Z)', content, re.DOTALL)
            if summary_match:
                summary = summary_match.group(1).strip()
            
            # 提取核心主题
            topics_match = re.search(r'### 🔑 核心主题\s*\n(.+?)(?=\n\s*---|\n\s*##|\Z)', content, re.DOTALL)
            if topics_match:
                topics_text = topics_match.group(1)
                for line in topics_text.strip().split('\n'):
                    if line.startswith('- ') or line.startswith('• '):
                        core_topics.append(line[2:].strip())
            
            return {
                "id": session_id,
                "file": str(file_path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "summary": summary,
                "core_topics": core_topics,
                "message_count": message_count
            }
        except Exception as e:
            return None
    
    def load_session(self, session_id):
        """加载指定会话"""
        # 支持模糊匹配
        pattern = re.compile(re.escape(session_id))
        
        for file in self.session_dir.glob("*.md"):
            if pattern.search(file.stem):
                self.current_file = file
                self.current_session = self._parse_markdown(file)
                return self.current_session
        
        return None
    
    def _parse_markdown(self, file_path):
        """解析Markdown文件为会话对象"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        session = {
            "id": file_path.stem,
            "messages": []
        }
        
        # 提取元数据
        import re
        
        # 提取消息数量
        msg_match = re.search(r'\*\*消息数量\*\*:\s*(\d+)', content)
        if msg_match:
            session["message_count"] = int(msg_match.group(1))
        
        # 提取摘要
        summary_match = re.search(r'## 📋 会话摘要\s*\n\s*\n(.+?)(?=\n\s*###|\n\s*---|\Z)', content, re.DOTALL)
        if summary_match:
            session["summary"] = summary_match.group(1).strip()
        
        # 提取核心主题
        topics_match = re.search(r'### 🔑 核心主题\s*\n(.+?)(?=\n\s*---|\n\s*##|\Z)', content, re.DOTALL)
        if topics_match:
            topics_text = topics_match.group(1)
            session["core_topics"] = []
            for line in topics_text.strip().split('\n'):
                if line.startswith('- ') or line.startswith('• '):
                    session["core_topics"].append(line[2:].strip())
        
        # 提取消息
        pattern = r'### .*? (USER|ASSISTANT) \[(.*?)\]\n\n(.*?)(?=\n\n---|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for role, timestamp, message_content in matches:
            session["messages"].append({
                "role": role.lower(),
                "content": message_content.strip(),
                "timestamp": timestamp
            })
        
        return session
    
    def get_current_messages(self):
        """获取当前会话的所有消息"""
        if self.current_session is None:
            return []
        return self.current_session["messages"]
    
    def get_formatted_history(self, max_messages=None):
        """获取格式化的历史记录，用于API调用"""
        messages = self.get_current_messages()
        if max_messages:
            messages = messages[-max_messages:]
        
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
    
    def format_sessions_for_display(self, sessions: List[Dict]) -> str:
        """格式化会话列表供用户选择"""
        if not sessions:
            return "暂无历史会话"
        
        lines = ["📚 历史会话列表:", ""]
        
        for i, session in enumerate(sessions, 1):
            lines.append(f"【{i}】 {session['id']}")
            
            # 显示摘要
            summary = session.get('summary', '暂无摘要')
            if summary and summary != '新会话 - 等待生成摘要':
                # 限制摘要长度
                if len(summary) > 80:
                    summary = summary[:80] + "..."
                lines.append(f"   📝 {summary}")
            
            # 显示核心主题
            core_topics = session.get('core_topics', [])
            if core_topics:
                topics_str = ', '.join(core_topics[:3])
                if len(core_topics) > 3:
                    topics_str += f" 等{len(core_topics)}个主题"
                lines.append(f"   🔑 {topics_str}")
            
            # 显示统计信息
            lines.append(f"   📊 消息: {session.get('message_count', 0)} | 时间: {session['modified'][:10]}")
            lines.append("")
        
        lines.append("输入 /load <序号> 或 /load <会话ID> 加载会话")
        return "\n".join(lines)
