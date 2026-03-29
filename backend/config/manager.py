"""Configuration Manager - 管理模型配置、安全开关、工作目录"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    base_url: str
    api_key: str
    model_name: str = "qwen-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7

@dataclass
class SecurityConfig:
    allow_command: bool = False
    command_timeout: int = 60
    dangerous_commands: list = None
    allowed_commands: list = None
    
    def __post_init__(self):
        if self.dangerous_commands is None:
            self.dangerous_commands = [
                'rm -rf /', 'rm -rf /*', 'rm -rf ~',
                'format', 'mkfs', 'dd if=/dev/zero',
                '> /dev/sda', 'mv / /dev/null',
                ':(){ :|:& };:', 'fork bomb',
                'del /f /s /q', 'rd /s /q',
                'powershell -enc', 'powershell -e ',
                'sudo rm', 'chmod 777 /',
            ]
        if self.allowed_commands is None:
            self.allowed_commands = []

@dataclass
class SystemConfig:
    work_dir: str
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    session_dir: str = "sessions"
    max_history: int = 100
    max_iterations: int = 10
    debug_mode: bool = False

class ConfigManager:
    CONFIG_FILE = "settings.json"
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / self.CONFIG_FILE
        self._config: Dict[str, Any] = {}
        self._load()
    
    def _load(self):
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        else:
            self._config = self._create_default()
            self._save()
    
    def _create_default(self) -> Dict[str, Any]:
        return {
            "model": {
                "base_url": "https://coding.dashscope.aliyuncs.com/v1",
                "api_key": "",
                "model_name": "qwen-turbo",
                "max_tokens": 2000,
                "temperature": 0.7
            },
            "security": {
                "allow_command": False,
                "command_timeout": 60,
                "dangerous_commands": [
                    'rm -rf /', 'rm -rf /*', 'rm -rf ~',
                    'format', 'mkfs', 'dd if=/dev/zero',
                    '> /dev/sda', 'mv / /dev/null',
                    ':(){ :|:& };:', 'fork bomb',
                    'del /f /s /q', 'rd /s /q',
                    'powershell -enc', 'powershell -e ',
                    'sudo rm', 'chmod 777 /',
                ],
                "allowed_commands": []
            },
            "system": {
                "work_dir": ".",
                "log_level": "INFO",
                "log_file": "logs/app.log",
                "session_dir": "sessions",
                "max_history": 100,
                "max_iterations": 10,
                "debug_mode": False
            }
        }
    
    def _save(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def get_model_config(self) -> ModelConfig:
        data = self._config.get("model", {})
        return ModelConfig(**data)
    
    def get_security_config(self) -> SecurityConfig:
        data = self._config.get("security", {})
        return SecurityConfig(**data)
    
    def get_system_config(self) -> SystemConfig:
        data = self._config.get("system", {})
        return SystemConfig(**data)
    
    def update_model_config(self, **kwargs):
        self._config["model"].update(kwargs)
        self._save()
    
    def update_security_config(self, **kwargs):
        self._config["security"].update(kwargs)
        self._save()
    
    def update_system_config(self, **kwargs):
        self._config["system"].update(kwargs)
        self._save()
    
    def get_all(self) -> Dict[str, Any]:
        return self._config.copy()
    
    def set_work_dir(self, work_dir: str):
        path = Path(work_dir).resolve()
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        self._config["system"]["work_dir"] = str(path)
        self._save()
    
    def get_work_dir(self) -> Path:
        return Path(self._config["system"]["work_dir"]).resolve()
    
    def is_command_allowed(self) -> bool:
        return self._config["security"]["allow_command"]
    
    def set_command_allowed(self, allowed: bool):
        self._config["security"]["allow_command"] = allowed
        self._save()