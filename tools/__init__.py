"""工具初始化模块"""
from .base import ToolRegistry
from .file_tools import WriteFileTool, ReadFileTool, DeleteFileTool, ListFilesTool
from .command_tools import ExecuteCommandTool, SearchFilesTool


def create_tool_registry() -> ToolRegistry:
    """创建并初始化工具注册表"""
    registry = ToolRegistry()
    
    # 注册文件操作工具
    registry.register(WriteFileTool())
    registry.register(ReadFileTool())
    registry.register(DeleteFileTool())
    registry.register(ListFilesTool())
    
    # 注册命令执行工具
    registry.register(ExecuteCommandTool())
    registry.register(SearchFilesTool())
    
    return registry


# 工具说明文档
TOOLS_DESCRIPTION = """
## 可用工具列表

### 文件操作工具
1. **write_file** - 写入文件
   - 参数: file_path, content, encoding
   - 用途: 创建或覆盖文件内容

2. **read_file** - 读取文件
   - 参数: file_path, encoding, limit, offset
   - 用途: 读取文件内容，支持分页

3. **delete_file** - 删除文件
   - 参数: file_path, recursive, confirm
   - 用途: 删除文件或目录

4. **list_files** - 列出文件
   - 参数: directory, pattern, recursive
   - 用途: 列出目录内容

### 命令执行工具
5. **execute_command** - 执行命令
   - 参数: command, working_dir, timeout
   - 用途: 执行终端命令

6. **search_files** - 搜索文件
   - 参数: pattern, directory, file_pattern, recursive
   - 用途: 在文件中搜索内容

## 使用方法
我会以ReAct格式思考，决定是否需要调用工具。
"""
