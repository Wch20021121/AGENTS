"""命令行执行工具"""
import subprocess
import shlex
from pathlib import Path
from typing import Dict, Any
from .base import BaseTool


class ExecuteCommandTool(BaseTool):
    """执行命令行工具"""
    
    name = "execute_command"
    description = """执行命令行命令，支持各种终端操作。注意：危险命令会被阻止。"""
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的命令"
            },
            "working_dir": {
                "type": "string",
                "description": "工作目录，默认为当前目录",
                "default": "."
            },
            "timeout": {
                "type": "integer",
                "description": "命令超时时间（秒），默认为60秒",
                "default": 60
            }
        },
        "required": ["command"]
    }
    
    # 危险命令黑名单
    DANGEROUS_COMMANDS = [
        'rm -rf /', 'rm -rf /*', 'rm -rf ~', 
        'format', 'mkfs', 'dd if=/dev/zero',
        '> /dev/sda', 'mv / /dev/null',
        ':(){ :|:& };:', 'fork bomb',
        'del /f /s /q', 'rd /s /q',
        'powershell -enc', 'powershell -e ',
    ]
    
    def is_dangerous(self, command: str) -> bool:
        """检查命令是否危险"""
        cmd_lower = command.lower().strip()
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous.lower() in cmd_lower:
                return True
        return False
    
    def execute(self, command: str, working_dir: str = ".", timeout: int = 60) -> str:
        # 安全检查
        if self.is_dangerous(command):
            return f"🚫 命令被阻止（危险操作）: {command}"
        
        try:
            work_path = Path(working_dir).resolve()
            
            if not work_path.exists():
                return f"❌ 工作目录不存在: {working_dir}"
            
            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            output = []
            output.append(f"📟 命令: {command}")
            output.append(f"📂 工作目录: {work_path}")
            output.append(f"⏱️  返回码: {result.returncode}")
            output.append("")
            
            if result.stdout:
                output.append("📤 标准输出:")
                output.append(result.stdout)
            
            if result.stderr:
                output.append("📥 标准错误:")
                output.append(result.stderr)
            
            if not result.stdout and not result.stderr:
                output.append("✅ 命令执行完成（无输出）")
            
            return "\n".join(output)
            
        except subprocess.TimeoutExpired:
            return f"⏱️ 命令执行超时（超过{timeout}秒）"
        except Exception as e:
            return f"❌ 命令执行失败: {str(e)}"


class SearchFilesTool(BaseTool):
    """搜索文件内容工具"""
    
    name = "search_files"
    description = "在文件中搜索指定内容，支持正则表达式"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "搜索模式（正则表达式）"
            },
            "directory": {
                "type": "string",
                "description": "搜索目录，默认为当前目录",
                "default": "."
            },
            "file_pattern": {
                "type": "string",
                "description": "文件匹配模式，如 *.py, *.txt",
                "default": "*"
            },
            "recursive": {
                "type": "boolean",
                "description": "是否递归搜索子目录",
                "default": True
            }
        },
        "required": ["pattern"]
    }
    
    def execute(self, pattern: str, directory: str = ".", file_pattern: str = "*", recursive: bool = True) -> str:
        try:
            import re
            from pathlib import Path
            
            path = Path(directory)
            if not path.exists():
                return f"❌ 目录不存在: {directory}"
            
            results = []
            match_count = 0
            file_count = 0
            
            if recursive:
                files = list(path.rglob(file_pattern))
            else:
                files = list(path.glob(file_pattern))
            
            regex = re.compile(pattern)
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        file_matches = []
                        for i, line in enumerate(lines, 1):
                            if regex.search(line):
                                file_matches.append((i, line.strip()))
                        
                        if file_matches:
                            file_count += 1
                            match_count += len(file_matches)
                            results.append(f"\n📄 {file_path.relative_to(path)}:")
                            for line_num, line_content in file_matches[:10]:  # 限制显示前10个匹配
                                results.append(f"  {line_num:4d}: {line_content}")
                            if len(file_matches) > 10:
                                results.append(f"  ... 还有 {len(file_matches) - 10} 个匹配")
                except Exception:
                    continue
            
            header = f"🔍 搜索结果: 模式 '{pattern}'\n"
            header += f"📂 目录: {path.absolute()}\n"
            header += f"📊 匹配文件: {file_count} | 匹配行数: {match_count}\n"
            header += "=" * 50
            
            if results:
                return header + "\n".join(results)
            else:
                return header + "\n\n📭 未找到匹配内容"
                
        except Exception as e:
            return f"❌ 搜索失败: {str(e)}"
