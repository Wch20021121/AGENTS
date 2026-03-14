"""
日志模块 - 支持多模块多日志文件的集中管理。

所有日志文件存储在 log/ 文件夹下，
不同模块可以写入不同的日志文件。
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """日志配置管理类。
    
    提供日志初始化、日志获取等静态方法，
    支持按模块分离日志文件。
    """
    
    LOG_DIR = Path("log")
    DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    _initialized = False
    _loggers: dict[str, logging.Logger] = {}
    
    @classmethod
    def init(cls, level: str = "INFO", console_output: bool = True) -> None:
        """初始化日志系统。
        
        Args:
            level: 日志级别，如 DEBUG/INFO/WARNING/ERROR。
            console_output: 是否同时输出到控制台。
        """
        if cls._initialized:
            return
        
        cls.LOG_DIR.mkdir(exist_ok=True)
        
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        file_formatter = logging.Formatter(cls.DEFAULT_FORMAT, datefmt=cls.DATE_FORMAT)
        
        if console_output:
            console_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt=cls.DATE_FORMAT
            )
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(log_level)
            
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)
            root_logger.addHandler(console_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, module_name: str) -> logging.Logger:
        """获取指定模块的日志记录器。
        
        Args:
            module_name: 模块名称，如 'chatbot', 'memory', 'main'。
        
        Returns:
            配置好的日志记录器实例。
        """
        if module_name in cls._loggers:
            return cls._loggers[module_name]
        
        logger = logging.getLogger(module_name)
        
        if logger.handlers:
            cls._loggers[module_name] = logger
            return logger
        
        log_file = cls.LOG_DIR / f"{module_name}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(cls.DEFAULT_FORMAT, datefmt=cls.DATE_FORMAT)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        
        cls._loggers[module_name] = logger
        return logger


def get_logger(module_name: str) -> logging.Logger:
    """便捷函数：获取指定模块的日志记录器。
    
    Args:
        module_name: 模块名称。
    
    Returns:
        配置好的日志记录器实例。
    """
    return LoggerConfig.get_logger(module_name)
