"""Logger Manager - 日志存储"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json

class LoggerManager:
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.log_file = self.log_dir / "app.log"
        self.tool_log_file = self.log_dir / "tools.log"
        self.security_log_file = self.log_dir / "security.log"
        
        self._setup_logging(log_level)
    
    def _setup_logging(self, log_level: str):
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("MiniAgent")
        self.tool_logger = logging.getLogger("MiniAgent.Tools")
        self.security_logger = logging.getLogger("MiniAgent.Security")
        
        self._setup_file_logger(self.tool_logger, self.tool_log_file, level)
        self._setup_file_logger(self.security_logger, self.security_log_file, level)
    
    def _setup_file_logger(self, logger: logging.Logger, file: Path, level: int):
        handler = logging.FileHandler(file, encoding='utf-8')
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    
    def log_tool_call(self, tool_name: str, params: Dict, result: Dict):
        self.tool_logger.info(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "params": params,
            "success": result.get("success", False),
            "message": result.get("message", "")
        }, ensure_ascii=False))
    
    def log_security_event(self, event_type: str, details: Dict):
        self.security_logger.warning(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }, ensure_ascii=False))
    
    def log_error(self, error: str, context: Dict = None):
        self.logger.error(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "context": context or {}
        }, ensure_ascii=False))
    
    def log_info(self, message: str):
        self.logger.info(message)