"""工具基类定义"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseTool(ABC):
    """工具基类"""
    
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """执行工具，返回结果字符串"""
        pass
    
    def to_function_schema(self) -> Dict[str, Any]:
        """转换为Function Calling的Schema格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        required = self.parameters.get("required", [])
        return all(param in params for param in required)


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> BaseTool:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的Schema"""
        return [tool.to_function_schema() for tool in self._tools.values()]
    
    def execute_tool(self, name: str, params: Dict[str, Any]) -> str:
        """执行指定工具"""
        tool = self.get(name)
        if not tool:
            return f"[错误] 未找到工具: {name}"
        
        if not tool.validate_params(params):
            return f"[错误] 工具 {name} 参数验证失败"
        
        try:
            return tool.execute(**params)
        except Exception as e:
            return f"[错误] 工具执行失败: {str(e)}"
