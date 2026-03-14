"""
模型数据类 - 用于传输模型相关数据。
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelData:
    """模型数据类。
    
    Attributes:
        id: 模型唯一标识符。
        provider: 模型提供商名称。
        description: 模型描述。
        user: 模型所有者（共享模型为 None）。
        is_shared: 是否共享。
    """
    id: str
    provider: str
    description: str
    user: Optional[str] = None
    is_shared: bool = False
    
    def to_dict(self) -> dict:
        """转换为字典（用于 JSON 序列化）。
        
        Returns:
            模型信息字典。
        """
        return {
            "id": self.id,
            "provider": self.provider,
            "description": self.description,
            "user": self.user,
            "is_shared": self.is_shared
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ModelData":
        """从字典创建 ModelData 实例。
        
        Args:
            data: 模型信息字典。
        
        Returns:
            ModelData 实例。
        """
        return cls(
            id=data.get("id", ""),
            provider=data.get("provider", ""),
            description=data.get("description", ""),
            user=data.get("user"),
            is_shared=data.get("is_shared", False)
        )
    
    def display_name(self) -> str:
        """获取显示名称。
        
        Returns:
            显示名称（provider 或 id）。
        """
        return self.provider if self.provider else self.id
    
    def is_owner(self, username: str) -> bool:
        """检查指定用户是否是模型所有者。
        
        Args:
            username: 用户名。
        
        Returns:
            是否是模型所有者。
        """
        return self.user == username
    
    def can_use(self, username: str, is_admin: bool = False) -> bool:
        """检查用户是否可以使用此模型。
        
        Args:
            username: 用户名。
            is_admin: 是否是管理员。
        
        Returns:
            是否可以使用。
        """
        if self.is_shared:
            return True
        if is_admin:
            return True
        return self.user == username
    
    def can_delete(self, username: str, is_admin: bool = False) -> bool:
        """检查用户是否可以删除此模型。
        
        Args:
            username: 用户名。
            is_admin: 是否是管理员。
        
        Returns:
            是否可以删除。
        """
        if is_admin:
            return True
        return self.user == username
    
    def owner_type(self) -> str:
        """获取所有者类型描述。
        
        Returns:
            所有者类型（共享/管理员/用户名）。
        """
        if self.is_shared:
            return "共享"
        elif self.user == "admin":
            return "管理员"
        else:
            return self.user or "未知"
