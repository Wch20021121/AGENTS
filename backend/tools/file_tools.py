"""File Tools - 文件操作工具"""
from pathlib import Path
from typing import Dict, Any, List
import os
import logging
from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

class WriteFileTool(BaseTool):
    name = "write_file"
    description = "写入文件到当前工作目录"
    permission_type = "write"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "相对工作目录的文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "文件内容"
                }
            },
            "required": ["file_path", "content"]
        }
    
    def execute(self, file_path: str, content: str, work_dir: str = ".") -> ToolResult:
        try:
            work_path = Path(work_dir).resolve()
            target_path = work_path / file_path
            
            if not self._is_safe_path(target_path, work_path):
                return ToolResult(
                    success=False,
                    tool=self.name,
                    error="path_not_allowed",
                    message="路径不在工作目录范围内"
                )
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            size = target_path.stat().st_size
            
            return ToolResult(
                success=True,
                tool=self.name,
                data={
                    "path": str(target_path),
                    "size": size,
                    "bytes_written": len(content.encode('utf-8'))
                },
                message=f"文件写入成功: {target_path}"
            )
        except Exception as e:
            logger.error(f"WriteFile error: {e}")
            return ToolResult(
                success=False,
                tool=self.name,
                error="write_error",
                message=str(e)
            )
    
    def _is_safe_path(self, target: Path, work_dir: Path) -> bool:
        try:
            target.resolve().relative_to(work_dir.resolve())
            return True
        except ValueError:
            return False


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "读取当前工作目录下的文件内容"
    permission_type = "read"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "相对工作目录的文件路径"
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str, work_dir: str = ".", limit: int = 0, offset: int = 1) -> ToolResult:
        try:
            work_path = Path(work_dir).resolve()
            target_path = work_path / file_path
            
            if not self._is_safe_path(target_path, work_path):
                return ToolResult(
                    success=False,
                    tool=self.name,
                    error="path_not_allowed",
                    message="路径不在工作目录范围内"
                )
            
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    tool=self.name,
                    error="file_not_found",
                    message=f"文件不存在: {file_path}"
                )
            
            if not target_path.is_file():
                return ToolResult(
                    success=False,
                    tool=self.name,
                    error="not_a_file",
                    message=f"路径不是文件: {file_path}"
                )
            
            with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            start_idx = max(0, offset - 1)
            end_idx = len(lines) if limit == 0 else min(start_idx + limit, len(lines))
            
            content = ''.join(lines[start_idx:end_idx])
            
            return ToolResult(
                success=True,
                tool=self.name,
                data={
                    "content": content,
                    "total_lines": total_lines,
                    "displayed_lines": f"{start_idx + 1}-{end_idx}",
                    "size": target_path.stat().st_size,
                    "path": str(target_path)
                },
                message=f"文件读取成功: {target_path}"
            )
        except Exception as e:
            logger.error(f"ReadFile error: {e}")
            return ToolResult(
                success=False,
                tool=self.name,
                error="read_error",
                message=str(e)
            )
    
    def _is_safe_path(self, target: Path, work_dir: Path) -> bool:
        try:
            target.resolve().relative_to(work_dir.resolve())
            return True
        except ValueError:
            return False


class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "检索或列出当前工作目录中的文件"
    permission_type = "read"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "检索关键词，可选"
                }
            },
            "required": []
        }
    
    def execute(self, keyword: str = None, work_dir: str = ".") -> ToolResult:
        try:
            work_path = Path(work_dir).resolve()
            
            if not work_path.exists():
                return ToolResult(
                    success=False,
                    tool=self.name,
                    error="dir_not_found",
                    message=f"工作目录不存在: {work_dir}"
                )
            
            files = []
            if keyword:
                for f in work_path.rglob("*"):
                    if f.is_file() and keyword.lower() in f.name.lower():
                        files.append({
                            "name": f.name,
                            "path": str(f.relative_to(work_path)),
                            "size": f.stat().st_size
                        })
            else:
                for f in work_path.glob("*"):
                    if f.is_file():
                        files.append({
                            "name": f.name,
                            "path": str(f.relative_to(work_path)),
                            "size": f.stat().st_size
                        })
            
            return ToolResult(
                success=True,
                tool=self.name,
                data={
                    "files": files,
                    "count": len(files),
                    "keyword": keyword
                },
                message=f"找到 {len(files)} 个文件"
            )
        except Exception as e:
            logger.error(f"SearchFiles error: {e}")
            return ToolResult(
                success=False,
                tool=self.name,
                error="search_error",
                message=str(e)
            )


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "删除当前工作目录下指定文件"
    permission_type = "delete"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "相对工作目录的文件路径"
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str, work_dir: str = ".") -> ToolResult:
        try:
            work_path = Path(work_dir).resolve()
            target_path = work_path / file_path
            
            if not self._is_safe_path(target_path, work_path):
                return ToolResult(
                    success=False,
                    tool=self.name,
                    error="path_not_allowed",
                    message="路径不在工作目录范围内"
                )
            
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    tool=self.name,
                    error="file_not_found",
                    message=f"文件不存在: {file_path}"
                )
            
            if target_path.is_file():
                target_path.unlink()
            elif target_path.is_dir():
                return ToolResult(
                    success=False,
                    tool=self.name,
                    error="is_directory",
                    message="当前版本不支持目录删除，请指定文件"
                )
            
            return ToolResult(
                success=True,
                tool=self.name,
                data={"path": str(target_path)},
                message=f"文件删除成功: {target_path}"
            )
        except Exception as e:
            logger.error(f"DeleteFile error: {e}")
            return ToolResult(
                success=False,
                tool=self.name,
                error="delete_error",
                message=str(e)
            )
    
    def _is_safe_path(self, target: Path, work_dir: Path) -> bool:
        try:
            target.resolve().relative_to(work_dir.resolve())
            return True
        except ValueError:
            return False