"""Command Tools - 命令执行工具"""
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import logging
from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

class RunCommandTool(BaseTool):
    name = "run_command"
    description = "执行受限制的安全命令行指令"
    permission_type = "execute"
    default_enabled = False
    
    DANGEROUS_COMMANDS = [
        'rm -rf /', 'rm -rf /*', 'rm -rf ~',
        'format', 'mkfs', 'dd if=/dev/zero',
        '> /dev/sda', 'mv / /dev/null',
        ':(){ :|:& };:', 'fork bomb',
        'del /f /s /q', 'rd /s /q',
        'powershell -enc', 'powershell -e ',
        'sudo rm', 'chmod 777 /',
        'wget', 'curl |', '| bash', '| sh',
    ]
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "命令字符串"
                }
            },
            "required": ["command"]
        }
    
    def execute(self, command: str, work_dir: str = ".", timeout: int = 60, 
                allow_command: bool = False, dangerous_commands: List[str] = None) -> ToolResult:
        if not allow_command:
            return ToolResult(
                success=False,
                tool=self.name,
                error="command_disabled",
                message="命令执行功能已禁用，请在配置中开启"
            )
        
        dangerous = dangerous_commands or self.DANGEROUS_COMMANDS
        if self._is_dangerous(command, dangerous):
            logger.warning(f"Blocked dangerous command: {command}")
            return ToolResult(
                success=False,
                tool=self.name,
                error="dangerous_command",
                message="命令被安全策略拦截"
            )
        
        try:
            work_path = Path(work_dir).resolve()
            
            if not work_path.exists():
                return ToolResult(
                    success=False,
                    tool=self.name,
                    error="dir_not_found",
                    message=f"工作目录不存在: {work_dir}"
                )
            
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
            
            return ToolResult(
                success=True,
                tool=self.name,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "command": command,
                    "work_dir": str(work_path)
                },
                message=f"命令执行完成，返回码: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                tool=self.name,
                error="timeout",
                message=f"命令执行超时（超过{timeout}秒）"
            )
        except Exception as e:
            logger.error(f"RunCommand error: {e}")
            return ToolResult(
                success=False,
                tool=self.name,
                error="execution_error",
                message=str(e)
            )
    
    def _is_dangerous(self, command: str, dangerous_list: List[str]) -> bool:
        cmd_lower = command.lower().strip()
        for dangerous in dangerous_list:
            if dangerous.lower() in cmd_lower:
                return True
        return False