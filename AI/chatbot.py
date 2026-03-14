"""
AI 聊天机器人模块 - 封装与 AI 模型的对话逻辑。
"""
import requests
from config import get_logger, ModelManager, API_KEY, BASE_URL, API_TEMPERATURE, API_TIMEOUT
from AI.memory import Memory
from users import UserManager
from users.user_manager import Admin, User
from users.data import UserData
from config.data import ModelData

logger = get_logger("chatbot")


class ChatbotContext:
    """聊天机器人上下文数据类。
    
    Attributes:
        user: 用户数据。
        model: 当前模型数据。
        api_key: 当前使用的 API 密钥。
        base_url: 当前使用的 API 基础 URL。
    """
    def __init__(self, user: UserData, model: ModelData, api_key: str, base_url: str):
        self.user = user
        self.model = model
        self.api_key = api_key
        self.base_url = base_url


class AIChatbot:
    """AI 对话助手核心类。
    
    封装与 AI 模型的 API 交互逻辑，
    管理对话历史和上下文。
    支持多用户数据隔离和独立 API 配置。
    
    共享模型使用系统 API 配置（环境变量），
    个人模型使用用户自己的 API 配置。
    """
    
    def __init__(self, user: Admin | User | None, user_mgr: UserManager, context_file: str = "chat_history.md"):
        """初始化聊天机器人。
        
        Args:
            user: 用户（Admin 或 User）。
            user_mgr: 用户管理器。
            context_file: 对话历史文件名。
        """
        if user is None:
            raise ValueError("用户不能为空")
        
        self.user = user
        self.user_mgr = user_mgr
        self.system_api_key = API_KEY
        self.system_base_url = BASE_URL
        
        # 转换为 UserData
        if isinstance(user, Admin):
            self.user_data = user.to_user_data()
        else:
            user_config = user_mgr.get_user_config(user.username)
            self.user_data = user.to_user_data(
                api_key=user_config.get('api_key'),
                base_url=user_config.get('base_url')
            )
        
        self.model_manager = ModelManager(user=self.user_data)
        self.memory = Memory(username=self.user_data.username, context_file=context_file)
        
        self._update_context()
        logger.info(f"聊天机器人初始化完成，用户：{self.user_data.username}, 当前模型：{self.model_manager.current_model_id}")
    
    def _get_current_model(self) -> ModelData:
        """获取当前模型数据。
        
        Returns:
            当前模型数据。
        """
        model_dict = None
        for m in self.model_manager.models:
            if m["id"] == self.model_manager.current_model_id:
                model_dict = m
                break
        
        if model_dict:
            return ModelData.from_dict(model_dict)
        return ModelData(id="", provider="", description="")
    
    def _update_context(self) -> None:
        """更新聊天机器人上下文（API 配置）。"""
        current_model = self._get_current_model()
        
        # 管理员总是使用系统 API
        if isinstance(self.user, Admin):
            api_key = self.system_api_key
            base_url = self.system_base_url
            logger.debug(f"管理员使用系统 API 配置")
        elif current_model.is_shared:
            # 普通用户使用共享模型时，检查是否有权限
            if self.user_mgr.can_use_shared_models():
                api_key = self.system_api_key
                base_url = self.system_base_url
                logger.debug(f"使用系统 API 配置（共享模型：{current_model.id}）")
            else:
                api_key = ""
                base_url = ""
                logger.warning("用户无权使用共享模型")
        else:
            # 个人模型使用用户自己的 API
            if self.user_mgr.can_use_personal_models():
                user_config = self.user_mgr.get_user_config(self.user_data.username)
                api_key = user_config.get("api_key", "")
                base_url = user_config.get("base_url", "")
                logger.debug(f"使用用户 API 配置（个人模型：{current_model.id}）")
            else:
                api_key = ""
                base_url = ""
                logger.warning("用户无权使用个人模型")
        
        self.context = ChatbotContext(
            user=self.user_data,
            model=current_model,
            api_key=api_key,
            base_url=base_url
        )
    
    def _check_api_config(self) -> str:
        """检查 API 配置。
        
        Returns:
            错误消息，如果配置正确则返回空字符串。
        """
        # 管理员总是可以使用所有模型
        if isinstance(self.user, Admin):
            if not self.system_api_key or not self.system_base_url:
                return "系统 API 配置缺失，请联系系统管理员"
            return ""
        
        # 普通用户检查
        if self.context.model.is_shared:
            # 检查是否有权限使用共享模型
            if not self.user_mgr.can_use_shared_models():
                return "您没有权限使用共享模型，请联系管理员"
            if not self.system_api_key or not self.system_base_url:
                return "系统 API 配置缺失"
            return ""
        else:
            # 检查是否有权限使用个人模型
            if not self.user_mgr.can_use_personal_models():
                return "您没有权限使用个人模型，请联系管理员"
            if not self.context.api_key or not self.context.base_url:
                return "请先配置个人 API（使用 setapi 命令）"
            return ""
    
    def chat(self, user_input: str) -> str:
        """发送用户消息并获取 AI 响应。
        
        Args:
            user_input: 用户输入的消息。
        
        Returns:
            AI 的响应消息，或错误提示。
        """
        self._update_context()
        
        error = self._check_api_config()
        if error:
            return f"错误：{error}"
        
        if not user_input.strip():
            logger.warning("收到空消息")
            return "请输入内容..."
        
        logger.debug(f"用户 {self.user_data.username} 输入：{user_input[:50]}...")
        self.memory.add("user", user_input)
        
        try:
            response = requests.post(
                f"{self.context.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.context.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.context.model.id,
                    "messages": self.memory.get_messages(),
                    "temperature": API_TEMPERATURE
                },
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            assistant_msg = result["choices"][0]["message"]["content"]
            
            logger.info(f"用户 {self.user_data.username} 收到 AI 响应：{assistant_msg[:50]}...")
            self.memory.add("assistant", assistant_msg)
            return assistant_msg
            
        except requests.Timeout as e:
            logger.error(f"用户 {self.user_data.username} 请求超时：{e}")
            return "请求超时，请稍后重试"
        except requests.RequestException as e:
            logger.error(f"用户 {self.user_data.username} 网络错误：{e}")
            return f"网络请求出错：{str(e)}"
        except Exception as e:
            logger.error(f"用户 {self.user.username} 未知错误：{e}")
            return f"请求出错：{str(e)}"
