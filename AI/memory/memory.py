"""
记忆模块 - 管理对话历史的存储与加载。

将对话记录以 Markdown 格式持久化存储，
支持消息数量限制和历史加载，支持多用户数据隔离。
"""
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import get_logger, MAX_MESSAGES

logger = get_logger("memory")


class Memory:
    """对话历史管理器。
    
    负责加载、保存和管理对话历史，
    支持限制最大消息数量以控制上下文长度。
    支持多用户数据隔离存储。
    
    Attributes:
        username: 用户名。
        context_file: 对话历史文件路径。
        max_messages: 最大保留的消息对数。
        messages: 当前加载的消息列表。
    """
    
    def __init__(self, username: str, context_file: str = "chat_history.md", max_messages: int = MAX_MESSAGES):
        """初始化记忆管理器。
        
        Args:
            username: 用户名。
            context_file: 对话历史文件名。
            max_messages: 最大保留的消息对数（默认 20）。
        """
        self.username = username
        self.max_messages = max_messages
        self.data_dir = Path(f"AI/memory/data/{username}")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.context_file = self.data_dir / context_file
        self.messages = self._load()
        logger.debug(f"记忆模块初始化完成，用户：{username}, 文件：{self.context_file}, 最大消息数：{max_messages}")
    
    def _load(self) -> list[dict[str, str]]:
        """从 markdown 文件加载历史记录。
        
        Returns:
            包含 system 消息和对话历史的消息列表。
        """
        messages = [{"role": "system", "content": "你是一个 helpful 的助手"}]
        
        file_path = Path(self.context_file)
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 兼容 Windows (CRLF) 和 Unix (LF) 行尾
                pattern = r'### (.+?)\r?\n\r?\n\*\*User:\*\*\s*(.+?)\r?\n\r?\n\*\*AI:\*\*\s*(.+?)\r?\n\r?\n---'
                matches = re.findall(pattern, content, re.DOTALL)
                
                for timestamp, user_msg, ai_msg in matches:
                    messages.append({"role": "user", "content": user_msg.strip()})
                    messages.append({"role": "assistant", "content": ai_msg.strip()})
                
                # 记录已保存的消息数量，用于后续追加
                self._saved_count = len(messages)
                
                logger.info(f"用户 {self.username} 加载了 {len(matches)} 条对话记录")
            except Exception as e:
                logger.error(f"加载历史文件失败：{e}")
                self._saved_count = 1
        else:
            logger.debug("历史文件不存在，创建新对话")
            self._saved_count = 1
        
        if len(messages) > self.max_messages + 1:
            messages = [messages[0]] + messages[-self.max_messages:]
            logger.debug(f"消息数量超过限制，已截断到最近 {self.max_messages} 条")
        
        return messages
    
    def save(self) -> None:
        """追加保存对话历史到 markdown 文件。
        
        将新增的消息追加到文件末尾，而不是覆写。
        """
        # 获取未保存的消息（从上次保存的位置开始）
        if hasattr(self, '_saved_count'):
            start_idx = self._saved_count
        else:
            # 第一次保存，检查文件是否已有内容
            if self.context_file.exists():
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 计算已有多少条对话
                pattern = r'### .+?\r?\n\r?\n\*\*User:\*\*'
                existing_count = len(re.findall(pattern, content))
                start_idx = existing_count * 2 + 1  # 每对对话 2 条消息 + system
            else:
                start_idx = 0
        
        if start_idx >= len(self.messages):
            return  # 没有新消息需要保存
        
        # 准备追加的内容
        append_content = ""
        if not self.context_file.exists() or start_idx == 0:
            append_content = "# 对话历史\n\n"
        
        i = 1 if start_idx == 0 else start_idx
        new_count = 0
        
        while i < len(self.messages):
            if self.messages[i]["role"] == "user" and i + 1 < len(self.messages):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_content = self.messages[i]["content"]
                assistant_content = self.messages[i + 1]["content"] if self.messages[i + 1]["role"] == "assistant" else ""
                
                append_content += f"### {timestamp}\n\n"
                append_content += f"**User:** {user_content}\n\n"
                append_content += f"**AI:** {assistant_content}\n\n"
                append_content += "---\n\n"
                new_count += 1
                i += 2
            else:
                i += 1
        
        if new_count > 0:
            try:
                with open(self.context_file, 'a', encoding='utf-8', newline='\n') as f:
                    f.write(append_content)
                self._saved_count = len(self.messages)
                logger.debug(f"用户 {self.username} 追加保存了 {new_count} 条对话记录到 {self.context_file}")
            except Exception as e:
                logger.error(f"保存历史文件失败：{e}")
    
    def add(self, role: str, content: str) -> None:
        """添加新消息到对话历史。
        
        Args:
            role: 消息角色（user/assistant/system）。
            content: 消息内容。
        """
        self.messages.append({"role": role, "content": content})
        
        if len(self.messages) > self.max_messages + 1:
            self.messages = [self.messages[0]] + self.messages[-self.max_messages:]
        
        self.save()
        logger.debug(f"用户 {self.username} 添加 {role} 消息，当前消息总数：{len(self.messages)}")
    
    def get_messages(self) -> list[dict[str, str]]:
        """获取完整的消息列表（包含 system 消息）。
        
        Returns:
            消息列表的副本。
        """
        return self.messages.copy()
    
    def clear(self) -> None:
        """清空对话历史。
        
        重置为仅包含 system 消息的初始状态，
        并删除历史文件。
        """
        self.messages = [{"role": "system", "content": "你是一个 helpful 的助手"}]
        
        try:
            Path(self.context_file).unlink(missing_ok=True)
            logger.info(f"用户 {self.username} 清空对话历史")
        except Exception as e:
            logger.error(f"删除历史文件失败：{e}")
    
    def get_history(self) -> str:
        """获取对话历史的文本摘要。
        
        Returns:
            格式化的对话历史摘要。
        """
        if len(self.messages) <= 1:
            return "暂无对话"
        
        lines = []
        idx = 1
        for msg in self.messages[1:]:
            role = "你" if msg["role"] == "user" else "AI"
            preview = msg['content'][:50] + ('...' if len(msg['content']) > 50 else '')
            lines.append(f"[{idx}] {role}: {preview}")
            if msg["role"] == "assistant":
                idx += 1
        
        logger.debug(f"用户 {self.username} 获取历史摘要，共 {idx-1} 条对话")
        return "\n".join(lines)
