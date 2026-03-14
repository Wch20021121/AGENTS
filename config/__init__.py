"""
配置包 - 集中管理应用配置和日志系统。
"""
from config.settings import (
    API_KEY,
    BASE_URL,
    API_TIMEOUT,
    API_TEMPERATURE,
    LOG_LEVEL,
    LOG_DIR,
    LOG_CONSOLE_OUTPUT,
    MODELS_PATH,
    CHAT_HISTORY_FILE,
    MAX_MESSAGES,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    ADMIN_SECRET_KEY,
    validate_config,
    ModelManager,
)
from config.logger import get_logger, LoggerConfig

__all__ = [
    # 配置常量
    "API_KEY",
    "BASE_URL",
    "API_TIMEOUT",
    "API_TEMPERATURE",
    "LOG_LEVEL",
    "LOG_DIR",
    "LOG_CONSOLE_OUTPUT",
    "MODELS_PATH",
    "CHAT_HISTORY_FILE",
    "MAX_MESSAGES",
    "ADMIN_USERNAME",
    "ADMIN_PASSWORD",
    "ADMIN_SECRET_KEY",
    # 配置函数
    "validate_config",
    # 模型管理
    "ModelManager",
    # 日志
    "get_logger",
    "LoggerConfig",
]
