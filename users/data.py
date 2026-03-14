"""
用户数据类 - 用于传输用户相关数据。
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class UserData:
    """用户数据类。
    
    Attributes:
        username: 用户名。
        is_admin: 是否为管理员。
        created_at: 创建时间。
        api_key: API 密钥（可选，用于个人模型）。
        base_url: API 基础 URL（可选，用于个人模型）。
    """
    username: str
    is_admin: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典（用于存储到 users.json）。
        
        Returns:
            用户信息字典（不包含 API 配置）。
        """
        return {
            "username": self.username,
            "is_admin": self.is_admin,
            "created_at": self.created_at
        }
    
    def to_config_dict(self) -> dict:
        """转换为配置字典（用于存储 API 配置）。
        
        Returns:
            API 配置字典。
        """
        return {
            "api_key": self.api_key or "",
            "base_url": self.base_url or ""
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserData":
        """从字典创建 UserData 实例。
        
        Args:
            data: 用户信息字典。
        
        Returns:
            UserData 实例。
        """
        return cls(
            username=data["username"],
            is_admin=data.get("is_admin", False),
            created_at=data.get("created_at", datetime.now().isoformat())
        )
    
    def has_personal_api(self) -> bool:
        """检查是否配置了个人 API。
        
        Returns:
            是否配置了个人 API。
        """
        return bool(self.api_key and self.base_url)
