"""Session Manager - 会话存储"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class Session:
    def __init__(self, session_id: str):
        self.id = session_id
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.messages: List[Dict[str, Any]] = []
        self.tool_calls: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            msg["metadata"] = metadata
        self.messages.append(msg)
        self.updated_at = datetime.now().isoformat()
    
    def add_tool_call(self, tool_name: str, params: Dict, result: Dict):
        call = {
            "tool": tool_name,
            "params": params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.tool_calls.append(call)
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": self.messages,
            "tool_calls": self.tool_calls
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        session = cls(data["id"])
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)
        session.messages = data.get("messages", [])
        session.tool_calls = data.get("tool_calls", [])
        return session

class SessionManager:
    def __init__(self, session_dir: str = "sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.current_session: Optional[Session] = None
    
    def create_session(self) -> str:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = Session(session_id)
        self._save_session()
        logger.info(f"Created session: {session_id}")
        return session_id
    
    def load_session(self, session_id: str) -> Optional[Session]:
        file = self.session_dir / f"{session_id}.json"
        if file.exists():
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.current_session = Session.from_dict(data)
            logger.info(f"Loaded session: {session_id}")
            return self.current_session
        return None
    
    def _save_session(self):
        if self.current_session:
            file = self.session_dir / f"{self.current_session.id}.json"
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(self.current_session.to_dict(), f, indent=2, ensure_ascii=False)
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        if not self.current_session:
            self.create_session()
        self.current_session.add_message(role, content, metadata)
        self._save_session()
    
    def add_tool_call(self, tool_name: str, params: Dict, result: Dict):
        if self.current_session:
            self.current_session.add_tool_call(tool_name, params, result)
            self._save_session()
    
    def get_messages(self, limit: int = None) -> List[Dict]:
        if not self.current_session:
            return []
        messages = self.current_session.messages
        if limit:
            messages = messages[-limit:]
        return messages
    
    def get_tool_calls(self) -> List[Dict]:
        if not self.current_session:
            return []
        return self.current_session.tool_calls
    
    def clear_current_session(self):
        if self.current_session:
            self.current_session.messages = []
            self.current_session.tool_calls = []
            self._save_session()
    
    def list_sessions(self) -> List[Dict]:
        sessions = []
        for file in self.session_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions.append({
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                    "message_count": len(data.get("messages", [])),
                    "tool_call_count": len(data.get("tool_calls", []))
                })
            except Exception as e:
                logger.error(f"Error loading session file: {e}")
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions
    
    def get_current_session_id(self) -> Optional[str]:
        return self.current_session.id if self.current_session else None