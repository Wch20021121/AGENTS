"""
用户管理模块 - 多用户系统核心。

功能：
- 用户创建、删除、切换
- 用户认证（密码验证）
- 管理员快速登录（admin <密钥>）
- 权限管理（管理员/普通用户）
- 用户数据存储
"""
import json
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime

from config import get_logger, ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_SECRET_KEY
from users.data import UserData

logger = get_logger("users")


class Admin:
    """管理员类 - 表示系统管理员。
    
    Attributes:
        username: 管理员用户名（固定为 admin）。
        created_at: 创建时间。
    """
    
    def __init__(self, created_at: Optional[str] = None):
        """初始化管理员。
        
        Args:
            created_at: 创建时间。
        """
        self.username = "admin"
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """转换为字典。
        
        Returns:
            管理员信息字典。
        """
        return {
            "username": self.username,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Admin":
        """从字典创建管理员。
        
        Args:
            data: 管理员信息字典。
        
        Returns:
            Admin 实例。
        """
        return cls(
            created_at=data.get("created_at")
        )
    
    def to_user_data(self) -> UserData:
        """转换为 UserData 数据类。
        
        Returns:
            UserData 实例（管理员）。
        """
        return UserData(
            username=self.username,
            is_admin=True,
            created_at=self.created_at
        )


class User:
    """用户类 - 表示普通用户。
    
    Attributes:
        username: 用户名。
        password_hash: 密码哈希。
        can_use_shared_models: 是否可以使用共享模型。
        can_use_personal_models: 是否可以使用个人模型。
        created_at: 创建时间。
    """
    
    def __init__(self, username: str, password_hash: str, 
                 can_use_shared_models: bool = True,
                 can_use_personal_models: bool = True,
                 created_at: Optional[str] = None):
        """初始化用户。
        
        Args:
            username: 用户名。
            password_hash: 密码哈希。
            can_use_shared_models: 是否可以使用共享模型。
            can_use_personal_models: 是否可以使用个人模型。
            created_at: 创建时间。
        """
        self.username = username
        self.password_hash = password_hash
        self.can_use_shared_models = can_use_shared_models
        self.can_use_personal_models = can_use_personal_models
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_user_data(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> UserData:
        """转换为 UserData 数据类。
        
        Args:
            api_key: API 密钥。
            base_url: API 基础 URL。
        
        Returns:
            UserData 实例。
        """
        return UserData(
            username=self.username,
            is_admin=False,
            created_at=self.created_at,
            api_key=api_key,
            base_url=base_url
        )
    
    def verify_password(self, password: str) -> bool:
        """验证密码。
        
        Args:
            password: 待验证的密码。
        
        Returns:
            密码是否正确。
        """
        return self.password_hash == self._hash_password(password)
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """哈希密码。
        
        Args:
            password: 明文密码。
        
        Returns:
            哈希后的密码。
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        """转换为字典。
        
        Returns:
            用户信息字典。
        """
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "can_use_shared_models": self.can_use_shared_models,
            "can_use_personal_models": self.can_use_personal_models,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """从字典创建用户。
        
        Args:
            data: 用户信息字典。
        
        Returns:
            User 实例。
        """
        return cls(
            username=data["username"],
            password_hash=data["password_hash"],
            can_use_shared_models=data.get("can_use_shared_models", True),
            can_use_personal_models=data.get("can_use_personal_models", True),
            created_at=data.get("created_at")
        )


class UserManager:
    """用户管理器 - 管理所有用户。
    
    Attributes:
        admin_file: 管理员数据文件路径。
        users_file: 用户数据文件路径。
        admin: 管理员实例。
        users: 用户字典。
        current_user: 当前登录用户（可以是 Admin 或 User）。
    """
    
    def __init__(self, admin_file: str = "users/admin.json", users_file: str = "users/users.json"):
        """初始化用户管理器。
        
        Args:
            admin_file: 管理员数据文件路径。
            users_file: 用户数据文件路径。
        """
        self.admin_file = Path(admin_file)
        self.users_file = Path(users_file)
        self.admin: Optional[Admin] = None
        self.users: dict[str, User] = {}
        self.current_user: Optional[Admin | User] = None
        self._load_data()
        self._init_admin()
        logger.info(f"用户管理器初始化完成，管理员：{1 if self.admin else 0} 个，普通用户：{len(self.users)} 个")
    
    def _load_data(self) -> None:
        """从文件加载管理员和用户数据。"""
        # 加载管理员
        if self.admin_file.exists():
            try:
                with open(self.admin_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.admin = Admin.from_dict(data)
                logger.info("加载了管理员")
            except Exception as e:
                logger.error(f"加载管理员数据失败：{e}")
                self.admin = None
        
        # 加载用户
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for username, user_data in data.items():
                    self.users[username] = User.from_dict(user_data)
                logger.info(f"加载了 {len(self.users)} 个用户")
            except Exception as e:
                logger.error(f"加载用户数据失败：{e}")
                self.users = {}
        else:
            self.users_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _save_admin(self) -> None:
        """保存管理员数据到文件。"""
        try:
            self.admin_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.admin_file, 'w', encoding='utf-8') as f:
                json.dump(self.admin.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug("管理员数据已保存")
        except Exception as e:
            logger.error(f"保存管理员数据失败：{e}")
    
    def _save_users(self) -> None:
        """保存用户数据到文件。"""
        try:
            data = {username: user.to_dict() for username, user in self.users.items()}
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("用户数据已保存")
        except Exception as e:
            logger.error(f"保存用户数据失败：{e}")
    
    def _init_admin(self) -> None:
        """初始化管理员账户。"""
        if self.admin is None:
            self.admin = Admin()
            self._save_admin()
            logger.info("创建管理员账户")
    
    def authenticate_admin(self, secret_key: str) -> bool:
        """管理员快速登录（使用密钥）。
        
        Args:
            secret_key: 管理员密钥。
        
        Returns:
            认证是否成功。
        """
        if secret_key == ADMIN_SECRET_KEY:
            self.current_user = self.admin
            logger.info("管理员使用密钥登录成功")
            return True
        else:
            logger.warning("管理员密钥错误")
            return False
    
    def authenticate(self, username: str, password: str) -> bool:
        """用户认证（普通用户）。
        
        Args:
            username: 用户名。
            password: 密码。
        
        Returns:
            认证是否成功。
        """
        user = self.users.get(username)
        if not user:
            logger.warning(f"认证失败：用户 {username} 不存在")
            return False
        
        if user.verify_password(password):
            self.current_user = user
            logger.info(f"用户 {username} 登录成功")
            return True
        else:
            logger.warning(f"认证失败：用户 {username} 密码错误")
            return False
    
    def create_user(self, username: str, password: str, 
                    can_use_shared_models: bool = True,
                    can_use_personal_models: bool = True,
                    operator: Admin | User = None) -> str:
        """创建新用户。
        
        Args:
            username: 新用户名。
            password: 密码。
            can_use_shared_models: 是否可以使用共享模型。
            can_use_personal_models: 是否可以使用个人模型。
            operator: 创建者用户。
        
        Returns:
            操作结果消息。
        """
        if not isinstance(operator, Admin):
            if isinstance(operator, User):
                logger.warning(f"用户 {operator.username} 尝试创建用户但无权限")
            return "错误：只有管理员可以创建用户"
        
        if username in self.users:
            logger.warning(f"创建用户失败：{username} 已存在")
            return f"用户 {username} 已存在"
        
        if not username or len(username) < 3:
            return "用户名至少 3 个字符"
        
        if len(password) < 6:
            return "密码至少 6 个字符"
        
        user = User(
            username=username,
            password_hash=User._hash_password(password),
            can_use_shared_models=can_use_shared_models,
            can_use_personal_models=can_use_personal_models
        )
        self.users[username] = user
        self._save_users()
        
        # 创建用户数据目录
        Path(f"AI/memory/data/{username}").mkdir(parents=True, exist_ok=True)
        
        logger.info(f"管理员创建用户：{username}")
        return f"用户 {username} 创建成功"
    
    def delete_user(self, username: str, operator: Admin | User = None) -> str:
        """删除用户。
        
        Args:
            username: 要删除的用户名。
            operator: 操作用户。
        
        Returns:
            操作结果消息。
        """
        if not isinstance(operator, Admin):
            if isinstance(operator, User):
                logger.warning(f"用户 {operator.username} 尝试删除用户但无权限")
            return "错误：只有管理员可以删除用户"
        
        if username not in self.users:
            return f"用户 {username} 不存在"
        
        if isinstance(self.current_user, User) and self.current_user.username == username:
            return "错误：不能删除当前登录用户"
        
        del self.users[username]
        self._save_users()
        
        # 删除用户数据目录
        user_data_dir = Path(f"AI/memory/data/{username}")
        if user_data_dir.exists():
            import shutil
            shutil.rmtree(user_data_dir)
        
        # 删除用户配置文件
        user_config_file = Path(f"config/users/{username}_config.json")
        if user_config_file.exists():
            user_config_file.unlink()
        
        logger.info(f"管理员删除用户：{username}")
        return f"用户 {username} 已删除"
    
    def set_user_permissions(self, username: str, 
                            can_use_shared_models: Optional[bool] = None,
                            can_use_personal_models: Optional[bool] = None,
                            operator: Admin | User = None) -> str:
        """设置用户权限。
        
        Args:
            username: 用户名。
            can_use_shared_models: 是否可以使用共享模型。
            can_use_personal_models: 是否可以使用个人模型。
            operator: 操作用户。
        
        Returns:
            操作结果消息。
        """
        if not isinstance(operator, Admin):
            return "错误：只有管理员可以设置用户权限"
        
        if username not in self.users:
            return f"用户 {username} 不存在"
        
        user = self.users[username]
        
        if can_use_shared_models is not None:
            user.can_use_shared_models = can_use_shared_models
        
        if can_use_personal_models is not None:
            user.can_use_personal_models = can_use_personal_models
        
        self._save_users()
        logger.info(f"管理员设置用户 {username} 权限：共享模型={user.can_use_shared_models}, 个人模型={user.can_use_personal_models}")
        return f"用户 {username} 权限已更新"
    
    def list_users(self) -> str:
        """列出所有用户。
        
        Returns:
            用户列表字符串。
        """
        lines = ["用户列表:"]
        lines.append(f"  - admin [管理员] (当前)" if isinstance(self.current_user, Admin) else "  - admin [管理员]")
        
        for username, user in sorted(self.users.items()):
            shared_mark = " [可共享模型]" if user.can_use_shared_models else ""
            personal_mark = " [可个人模型]" if user.can_use_personal_models else ""
            current_mark = " (当前)" if isinstance(self.current_user, User) and self.current_user.username == username else ""
            lines.append(f"  - {username}{shared_mark}{personal_mark}{current_mark}")
        
        return "\n".join(lines)
    
    def logout(self) -> None:
        """登出当前用户。"""
        if self.current_user:
            username = self.current_user.username if hasattr(self.current_user, 'username') else 'admin'
            logger.info(f"用户 {username} 登出")
            self.current_user = None
    
    def get_user_data_dir(self, username: Optional[str] = None) -> Path:
        """获取用户数据目录。
        
        Args:
            username: 用户名，默认为当前用户。
        
        Returns:
            用户数据目录路径。
        
        Raises:
            ValueError: 当没有指定用户且未登录时。
        """
        if username is None:
            if not self.current_user:
                raise ValueError("未登录用户")
            username = self.current_user.username if hasattr(self.current_user, 'username') else 'admin'
        
        data_dir = Path(f"AI/memory/data/{username}")
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def get_user_config(self, username: Optional[str] = None) -> dict:
        """获取用户配置。
        
        Args:
            username: 用户名，默认为当前用户。
        
        Returns:
            用户配置字典（包含 api_key, base_url）。
        """
        if username is None:
            if not self.current_user:
                raise ValueError("未登录用户")
            username = self.current_user.username if hasattr(self.current_user, 'username') else 'admin'
        
        config_file = Path(f"config/users/{username}_config.json")
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {"api_key": "", "base_url": ""}
    
    def set_user_config(self, api_key: str, base_url: str, username: Optional[str] = None) -> str:
        """设置用户配置。
        
        Args:
            api_key: API 密钥。
            base_url: API 基础 URL。
            username: 用户名，默认为当前用户。
        
        Returns:
            操作结果消息。
        """
        if username is None:
            if not self.current_user:
                raise ValueError("未登录用户")
            username = self.current_user.username if hasattr(self.current_user, 'username') else 'admin'
        
        config_file = Path(f"config/users/{username}_config.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            "api_key": api_key,
            "base_url": base_url
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"用户 {username} API 配置已更新")
        return "个人 API 配置已保存（仅用于个人模型）"
    
    def can_use_shared_models(self) -> bool:
        """检查当前用户是否可以使用共享模型。
        
        Returns:
            是否可以使用共享模型。
        """
        if isinstance(self.current_user, Admin):
            return True
        if isinstance(self.current_user, User):
            return self.current_user.can_use_shared_models
        return False
    
    def can_use_personal_models(self) -> bool:
        """检查当前用户是否可以使用个人模型。
        
        Returns:
            是否可以使用个人模型。
        """
        if isinstance(self.current_user, Admin):
            return True
        if isinstance(self.current_user, User):
            return self.current_user.can_use_personal_models
        return False
