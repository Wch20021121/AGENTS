"""API Routes - 接口层"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from typing import Dict, Any
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ..config.manager import ConfigManager
from ..storage.session import SessionManager
from ..storage.logger import LoggerManager
from ..tools.registry import ToolRegistry
from ..tools.file_tools import WriteFileTool, ReadFileTool, SearchFilesTool, DeleteFileTool
from ..tools.command_tools import RunCommandTool
from ..core.agent import AgentCore
from ..services.commands import CommandHandler

logger = logging.getLogger(__name__)

def create_app(config_dir: str = "config") -> Flask:
    app = Flask(__name__)
    CORS(app)
    
    config_manager = ConfigManager(config_dir)
    system_config = config_manager.get_system_config()
    
    logger_manager = LoggerManager(
        log_dir=Path(system_config.log_file).parent,
        log_level=system_config.log_level
    )
    
    session_manager = SessionManager(system_config.session_dir)
    
    tool_registry = ToolRegistry()
    tool_registry.register(WriteFileTool())
    tool_registry.register(ReadFileTool())
    tool_registry.register(SearchFilesTool())
    tool_registry.register(DeleteFileTool())
    tool_registry.register(RunCommandTool())
    
    agent_core = AgentCore(config_manager, session_manager, tool_registry, logger_manager)
    
    command_handler = CommandHandler(config_manager, session_manager, tool_registry, agent_core)
    
    @app.route('/chat', methods=['POST'])
    def chat():
        data = request.get_json()
        user_input = data.get('message', '')
        
        if not user_input:
            return jsonify({"error": "message required"}), 400
        
        if command_handler.is_command(user_input):
            result = command_handler.handle(user_input)
            return jsonify(result)
        
        try:
            result = agent_core.process(user_input)
            return jsonify({
                "type": "chat_result",
                "response": result["response"],
                "tool_calls": result["tool_calls"],
                "session_id": result["session_id"]
            })
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/sessions', methods=['GET'])
    def list_sessions():
        sessions = session_manager.list_sessions()
        return jsonify({"sessions": sessions})
    
    @app.route('/sessions', methods=['POST'])
    def create_session():
        session_id = session_manager.create_session()
        return jsonify({"session_id": session_id})
    
    @app.route('/sessions/<session_id>', methods=['GET'])
    def get_session(session_id):
        session = session_manager.load_session(session_id)
        if session:
            return jsonify(session.to_dict())
        return jsonify({"error": "session not found"}), 404
    
    @app.route('/config', methods=['GET'])
    def get_config():
        return jsonify(config_manager.get_all())
    
    @app.route('/config', methods=['POST'])
    def update_config():
        data = request.get_json()
        section = data.get('section', '')
        updates = data.get('updates', {})
        
        if section == 'model':
            config_manager.update_model_config(**updates)
        elif section == 'security':
            config_manager.update_security_config(**updates)
        elif section == 'system':
            config_manager.update_system_config(**updates)
        else:
            return jsonify({"error": "invalid section"}), 400
        
        return jsonify({"success": True, "config": config_manager.get_all()})
    
    @app.route('/tools', methods=['GET'])
    def list_tools():
        tools = tool_registry.get_all_metadata()
        return jsonify({"tools": tools})
    
    @app.route('/status', methods=['GET'])
    def get_status():
        model_ok = agent_core.test_connection()
        security = config_manager.get_security_config()
        session_id = session_manager.get_current_session_id()
        
        return jsonify({
            "model_connected": model_ok,
            "command_allowed": security.allow_command,
            "session_id": session_id,
            "work_dir": str(config_manager.get_work_dir()),
            "tools_count": len(tool_registry.list_tools())
        })
    
    @app.route('/')
    def index():
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        index_path = frontend_dir / 'index.html'
        if index_path.exists():
            return index_path.read_text(encoding='utf-8')
        return "index.html not found", 404
    
    return app