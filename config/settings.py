"""
配置管理模块 - 集中管理所有应用配置。

配置分区：
- API 配置：API 密钥、基础 URL 等
- 日志配置：日志级别、日志目录等
- 模型配置：模型文件路径、模型管理
- 对话配置：历史文件、最大消息数等
"""
import os
import json
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

from config.logger import get_logger
from config.data import ModelData

logger = get_logger("config")

# ============================================================
# 初始化环境变量
# ============================================================
load_dotenv()


# ============================================================
# API 配置
# ============================================================
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
API_TEMPERATURE = float(os.getenv("API_TEMPERATURE", "0.7"))


# ============================================================
# 日志配置
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "log")
LOG_CONSOLE_OUTPUT = os.getenv("LOG_CONSOLE_OUTPUT", "true").lower() in ("true", "1", "yes")


# ============================================================
# 模型配置
# ============================================================
MODELS_PATH = os.getenv("MODELS_PATH", "config/models.json")


# ============================================================
# 对话配置
# ============================================================
CHAT_HISTORY_FILE = os.getenv("CHAT_HISTORY_FILE", "chat_history.md")
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "20"))


# ============================================================
# 管理员配置
# ============================================================
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "111111")  # 管理员快速登录密钥


# ============================================================
# 配置验证
# ============================================================
def validate_config() -> None:
    """验证必要配置是否存在。
    
    Raises:
        ValueError: 当必要配置缺失时抛出异常。
    """
    if not API_KEY:
        raise ValueError("请在 .env 文件中配置 API_KEY")
    if not BASE_URL:
        raise ValueError("请在 .env 文件中配置 BASE_URL")
    if not Path(MODELS_PATH).exists():
        raise ValueError(f"模型配置文件不存在：{MODELS_PATH}")


# ============================================================
# 模型管理器
# ============================================================
class ModelManager:
    """管理可用模型列表，支持添加、删除、切换模型。
    
    所有模型存储在同一文件中，通过 user 和 is_shared 字段区分。
    - user: 模型提供者（用户名），共享模型为 null
    - is_shared: 是否为共享模型
    
    Attributes:
        user: 当前用户。
        models_path: 模型配置文件路径。
        models: 模型列表。
        model_index: 当前选中模型的索引。
    """
    
    def __init__(self, user=None, models_path: str = MODELS_PATH):
        """初始化模型管理器。
        
        Args:
            user: 当前用户。
            models_path: 模型配置文件路径。
        """
        self.user = user
        self.models_path = Path(models_path)
        self.models_data: List[ModelData] = self._load_models()
        self.model_index = 0
    
    def _load_models(self) -> List[ModelData]:
        """从配置文件加载模型列表。
        
        加载所有模型，包括共享模型和用户模型。
        模型格式：JSON 数组
        
        Returns:
            ModelData 列表。
        """
        models = []
        path = self.models_path
        
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        model = ModelData.from_dict(item)
                        models.append(model)
            except Exception as e:
                logger.error(f"加载模型文件失败：{e}")
        
        return models
    
    @property
    def models(self) -> List[dict]:
        """获取模型字典列表（向后兼容）。
        
        Returns:
            模型字典列表。
        """
        return [m.to_dict() for m in self.models_data]
    
    def _save_models(self) -> None:
        """保存模型列表到配置文件（JSON 格式）。"""
        self.models_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = [m.to_dict() for m in self.models_data]
        
        with open(self.models_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _get_visible_models(self) -> List[ModelData]:
        """获取当前用户可见的模型列表。
        
        Returns:
            可见模型列表。
        """
        if not self.user:
            return [m for m in self.models_data if m.is_shared]
        
        if self.user.is_admin:
            return self.models_data
        
        return [m for m in self.models_data if m.is_shared or m.user == self.user.username]
    
    @property
    def current_model_id(self) -> str:
        """获取当前选中模型的 ID。
        
        Returns:
            当前模型 ID。
        
        Raises:
            ValueError: 当没有可用模型时抛出异常。
        """
        visible_models = self._get_visible_models()
        if not visible_models:
            raise ValueError("没有可用的模型，请先添加模型")
        return visible_models[self.model_index].id
    
    def list_models(self) -> str:
        """列出所有可用模型。
        
        Returns:
            格式化的模型列表字符串。
        """
        visible_models = self._get_visible_models()
        
        if not visible_models:
            return "暂无可用模型，请使用 'addmodel' 命令添加模型"
        
        lines = ["可用模型列表:"]
        for i, m in enumerate(visible_models):
            current = " (当前)" if i == self.model_index else ""
            owner = m.owner_type()
            lines.append(f"  [{i}] {m.display_name()} ({m.id}) - {m.description} [{owner}]{current}")
        lines.append("\n命令：models <编号> 切换 | addmodel <id> <name> <desc> [--shared] | delmodel <编号> 删除")
        return "\n".join(lines)
    
    def set_model(self, index: int) -> str:
        """切换到指定模型。
        
        Args:
            index: 模型列表中的索引。
        
        Returns:
            切换结果消息。
        """
        visible_models = self._get_visible_models()
        if 0 <= index < len(visible_models):
            self.model_index = index
            model = visible_models[index]
            return f"已切换模型：{model.display_name()} ({model.id})"
        return f"无效编号，请输入 0-{len(visible_models)-1}"
    
    def add_model(self, model_id: str, name: str, description: str = "", shared: bool = False) -> str:
        """添加新模型。
        
        Args:
            model_id: 模型 ID。
            name: 模型名称。
            description: 模型描述。
            shared: 是否为共享模型（仅管理员可用）。
        
        Returns:
            添加结果消息。
        """
        for m in self.models_data:
            if m.id == model_id:
                return f"模型 {model_id} 已存在"
        
        if shared:
            if self.user and not self.user.is_admin:
                return "错误：只有管理员可以添加共享模型"
            user_field = self.user.username if self.user else "admin"
        else:
            user_field = self.user.username if self.user else None
        
        model = ModelData(
            id=model_id,
            provider=name,
            description=description,
            user=user_field,
            is_shared=shared
        )
        
        self.models_data.append(model)
        self._save_models()
        return f"已添加模型：{name} ({model_id})"
    
    def remove_model(self, index: int, operator=None) -> str:
        """删除指定模型。
        
        Args:
            index: 模型列表中的索引。
            operator: 操作用户。
        
        Returns:
            删除结果消息。
        """
        visible_models = self._get_visible_models()
        if 0 <= index < len(visible_models):
            if len(visible_models) == 1:
                return "至少保留一个模型"
            
            model = visible_models[index]
            
            if model.is_shared:
                if not operator or not operator.is_admin:
                    return "错误：只有管理员可以删除共享模型"
            else:
                if operator and model.user != operator.username and not operator.is_admin:
                    return "错误：不能删除其他用户的模型"
            
            self.models_data.remove(model)
            self._save_models()
            
            visible_models_after = self._get_visible_models()
            if self.model_index >= len(visible_models_after):
                self.model_index = len(visible_models_after) - 1
            
            return f"已删除模型：{model.display_name()} ({model.id})"
        return f"无效编号，请输入 0-{len(visible_models)-1}"
    
    def get_model_info(self) -> str:
        """获取当前模型信息。
        
        Returns:
            当前模型信息字符串。
        """
        visible_models = self._get_visible_models()
        if not visible_models:
            return "当前无模型"
        m = visible_models[self.model_index]
        return f"当前模型：{m.display_name()} ({m.id}) - {m.description}"
