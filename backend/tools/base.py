"""Tool Base Class - 工具基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    success: bool
    tool: str
    data: Any = None
    error: str = None
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "tool": self.tool,
            "data": self.data,
            "error": self.error,
            "message": self.message
        }

class BaseTool(ABC):
    name: str = ""
    description: str = ""
    permission_type: str = "read"
    default_enabled: bool = True
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        pass
    
    def to_function_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        required = self.parameters.get("required", [])
        return all(param in params for param in required)
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "permission_type": self.permission_type,
            "default_enabled": self.default_enabled
        }