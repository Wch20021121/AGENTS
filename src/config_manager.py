"""配置管理模块"""
import json
import os
from pathlib import Path


class ConfigManager:
    """管理API配置和系统设置"""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.api_config_file = self.config_dir / "api_config.json"
        self.settings_file = self.config_dir / "settings.json"
        self._api_config = None
        self._settings = None
    
    def load_api_config(self):
        """加载API配置"""
        if self._api_config is None:
            if self.api_config_file.exists():
                with open(self.api_config_file, 'r', encoding='utf-8') as f:
                    self._api_config = json.load(f)
            else:
                self._api_config = self._create_default_api_config()
        return self._api_config
    
    def load_settings(self):
        """加载系统设置"""
        if self._settings is None:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
            else:
                self._settings = self._create_default_settings()
        return self._settings
    
    def get_current_provider(self):
        """获取当前使用的API提供商配置"""
        config = self.load_api_config()
        default_provider = config.get("default", "dashscope")
        return config["providers"].get(default_provider)
    
    def set_provider(self, provider_name):
        """设置当前API提供商"""
        config = self.load_api_config()
        if provider_name in config.get("providers", {}):
            config["default"] = provider_name
            self.save_api_config(config)
            return True
        return False
    
    def add_provider(self, name, base_url, api_key):
        """添加新的API提供商"""
        config = self.load_api_config()
        if "providers" not in config:
            config["providers"] = {}
        config["providers"][name] = {
            "base_url": base_url,
            "api_key": api_key
        }
        self.save_api_config(config)
    
    def save_api_config(self, config):
        """保存API配置"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.api_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        self._api_config = config
    
    def save_settings(self, settings):
        """保存系统设置"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        self._settings = settings
    
    def _create_default_api_config(self):
        """创建默认API配置"""
        config = {
            "default": "dashscope",
            "providers": {
                "dashscope": {
                    "base_url": "https://coding.dashscope.aliyuncs.com/v1",
                    "api_key": ""
                }
            }
        }
        self.save_api_config(config)
        return config
    
    def _create_default_settings(self):
        """创建默认系统设置"""
        settings = {
            "log_level": "INFO",
            "log_file": "logs/app.log",
            "session_dir": "sessions",
            "max_history": 100
        }
        self.save_settings(settings)
        return settings
