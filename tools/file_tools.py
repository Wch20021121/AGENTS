"""文件操作工具"""
import os
from pathlib import Path
from typing import Dict, Any
from .base import BaseTool


class WriteFileTool(BaseTool):
    """写入文件工具"""
    
    name = "write_file"
    description = "写入内容到指定文件，如果文件不存在则创建，存在则覆盖"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "文件路径，可以是相对路径或绝对路径"
            },
            "content": {
                "type": "string",
                "description": "要写入的文件内容"
            },
            "encoding": {
                "type": "string",
                "description": "文件编码，默认为utf-8",
                "default": "utf-8"
            }
        },
        "required": ["file_path", "content"]
    }
    
    def execute(self, file_path: str, content: str, encoding: str = "utf-8") -> str:
        try:
            # 处理路径
            path = Path(file_path)
            
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # 获取文件信息
            size = path.stat().st_size
            abs_path = path.absolute()
            
            return f"✅ 文件写入成功\n路径: {abs_path}\n大小: {size} bytes\n字符数: {len(content)}"
        except Exception as e:
            return f"❌ 文件写入失败: {str(e)}"


class ReadFileTool(BaseTool):
    """读取文件工具"""
    
    name = "read_file"
    description = "读取指定文件的内容，支持文本文件"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "文件路径，可以是相对路径或绝对路径"
            },
            "encoding": {
                "type": "string",
                "description": "文件编码，默认为utf-8",
                "default": "utf-8"
            },
            "limit": {
                "type": "integer",
                "description": "限制读取的最大行数，0表示不限制",
                "default": 0
            },
            "offset": {
                "type": "integer",
                "description": "从第几行开始读取（1-based），默认为1",
                "default": 1
            }
        },
        "required": ["file_path"]
    }
    
    def execute(self, file_path: str, encoding: str = "utf-8", limit: int = 0, offset: int = 1) -> str:
        try:
            path = Path(file_path)
            
            if not path.exists():
                return f"❌ 文件不存在: {file_path}"
            
            if not path.is_file():
                return f"❌ 路径不是文件: {file_path}"
            
            with open(path, 'r', encoding=encoding, errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # 应用偏移和限制
            start_idx = max(0, offset - 1)
            end_idx = len(lines) if limit == 0 else min(start_idx + limit, len(lines))
            selected_lines = lines[start_idx:end_idx]
            
            content = ''.join(selected_lines)
            actual_start = start_idx + 1
            actual_end = end_idx
            
            result = f"📄 文件: {path.absolute()}\n"
            result += f"总行数: {total_lines} | 显示: 第{actual_start}-{actual_end}行\n"
            result += "=" * 50 + "\n\n"
            result += content
            
            return result
        except Exception as e:
            return f"❌ 文件读取失败: {str(e)}"


class DeleteFileTool(BaseTool):
    """删除文件工具"""
    
    name = "delete_file"
    description = "删除指定的文件或目录，删除目录时需要确认recursive参数"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要删除的文件或目录路径"
            },
            "recursive": {
                "type": "boolean",
                "description": "是否递归删除目录及其内容，默认为false",
                "default": False
            },
            "confirm": {
                "type": "boolean",
                "description": "确认删除，必须设置为true才会执行",
                "default": False
            }
        },
        "required": ["file_path"]
    }
    
    def execute(self, file_path: str, recursive: bool = False, confirm: bool = False) -> str:
        if not confirm:
            return "⚠️ 删除操作需要设置 confirm=true 才会执行"
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                return f"❌ 路径不存在: {file_path}"
            
            abs_path = path.absolute()
            
            if path.is_file():
                path.unlink()
                return f"✅ 文件已删除: {abs_path}"
            elif path.is_dir():
                if recursive:
                    import shutil
                    shutil.rmtree(path)
                    return f"✅ 目录及内容已删除: {abs_path}"
                else:
                    return f"⚠️ 这是目录，如需删除请设置 recursive=true\n路径: {abs_path}"
            else:
                return f"❌ 未知类型的路径: {abs_path}"
        except Exception as e:
            return f"❌ 删除失败: {str(e)}"


class ListFilesTool(BaseTool):
    """列出文件工具"""
    
    name = "list_files"
    description = "列出指定目录下的文件和子目录，支持通配符匹配"
    parameters = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "目录路径，默认为当前目录",
                "default": "."
            },
            "pattern": {
                "type": "string",
                "description": "文件匹配模式，如 *.py, *.txt",
                "default": "*"
            },
            "recursive": {
                "type": "boolean",
                "description": "是否递归列出子目录",
                "default": False
            }
        },
        "required": []
    }
    
    def execute(self, directory: str = ".", pattern: str = "*", recursive: bool = False) -> str:
        try:
            path = Path(directory)
            
            if not path.exists():
                return f"❌ 目录不存在: {directory}"
            
            if not path.is_dir():
                return f"❌ 路径不是目录: {directory}"
            
            result_lines = [f"📁 目录: {path.absolute()}", ""]
            
            if recursive:
                files = list(path.rglob(pattern))
            else:
                files = list(path.glob(pattern))
            
            # 分类显示
            dirs = [f for f in files if f.is_dir()]
            files_only = [f for f in files if f.is_file()]
            
            if dirs:
                result_lines.append("📂 子目录:")
                for d in sorted(dirs):
                    depth = len(d.relative_to(path).parts) - 1
                    indent = "  " * depth
                    result_lines.append(f"  {indent}📁 {d.name}")
                result_lines.append("")
            
            if files_only:
                result_lines.append("📄 文件:")
                for f in sorted(files_only):
                    size = f.stat().st_size
                    size_str = f"{size:,} bytes"
                    result_lines.append(f"  📄 {f.name} ({size_str})")
            
            if not dirs and not files_only:
                result_lines.append("📭 目录为空")
            
            return "\n".join(result_lines)
        except Exception as e:
            return f"❌ 列出文件失败: {str(e)}"
