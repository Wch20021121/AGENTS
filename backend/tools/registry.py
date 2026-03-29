"""Tool Registry - 工具注册表"""
from typing import Dict, List, Any
from .base import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get(self, name: str) -> BaseTool:
        return self._tools.get(name)
    
    def has(self, name: str) -> bool:
        return name in self._tools
    
    def list_tools(self) -> List[str]:
        return list(self._tools.keys())
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_function_schema() for tool in self._tools.values()]
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        return [tool.get_metadata() for tool in self._tools.values()]
    
    def execute(self, name: str, params: Dict[str, Any]) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                tool=name,
                error="tool_not_found",
                message=f"Tool '{name}' not found"
            )
        
        if not tool.validate_params(params):
            required = tool.parameters.get("required", [])
            missing = [p for p in required if p not in params]
            return ToolResult(
                success=False,
                tool=name,
                error="invalid_params",
                message=f"Missing required parameters: {missing}"
            )
        
        try:
            result = tool.execute(**params)
            logger.info(f"Tool '{name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{name}' execution failed: {e}")
            return ToolResult(
                success=False,
                tool=name,
                error="execution_error",
                message=str(e)
            )