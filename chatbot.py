import requests
from pathlib import Path
from memory import Memory
from config import API_KEY, BASE_URL, MODELS_PATH

class AIChatbot:
    def __init__(self, context_file="chat_history.md", model_index=0):
        self.api_key = API_KEY
        self.base_url = BASE_URL
        self.models_path = MODELS_PATH
        self.models = self._load_models()
        self.model_index = min(model_index, len(self.models) - 1) if self.models else 0
        self.memory = Memory(context_file)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if not self.api_key or not self.base_url:
            raise ValueError("请在 .env 文件中配置 API_KEY 和 BASE_URL")
    
    def _load_models(self) -> list[dict]:
        models = []
        
        if Path(self.models_path).exists():
            with open(self.models_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[1:]:
                    line = line.strip()
                    if line and ',' in line:
                        parts = line.split(',', 2)
                        if len(parts) >= 2:
                            models.append({
                                "id": parts[0].strip(),
                                "name": parts[1].strip(),
                                "description": parts[2].strip() if len(parts) > 2 else ""
                            })
        
        return models
    
    def _save_models(self) -> None:
        with open(self.models_path, 'w', encoding='utf-8') as f:
            f.write("id,provider,description\n")
            for m in self.models:
                f.write(f"{m['id']},{m['name']},{m['description']}\n")
    
    @property
    def model(self) -> str:
        if not self.models:
            raise ValueError("没有可用的模型，请使用 'addmodel' 命令添加模型")
        return self.models[self.model_index]["id"]
    
    def list_models(self) -> str:
        if not self.models:
            return "暂无可用模型，请使用 'addmodel' 命令添加模型"
        
        lines = ["可用模型列表:"]
        for i, m in enumerate(self.models):
            current = " (当前)" if i == self.model_index else ""
            lines.append(f"  [{i}] {m['name']} ({m['id']}) - {m['description']}{current}")
        lines.append("\n命令: models <编号> 切换 | addmodel <id> <name> <desc> 添加 | delmodel <编号> 删除")
        return "\n".join(lines)
    
    def set_model(self, index: int) -> str:
        if 0 <= index < len(self.models):
            self.model_index = index
            model = self.models[index]
            return f"已切换模型: {model['name']} ({model['id']})"
        return f"无效编号，请输入 0-{len(self.models)-1}"
    
    def add_model(self, model_id: str, name: str, description: str = "") -> str:
        # 检查是否已存在
        for m in self.models:
            if m["id"] == model_id:
                return f"模型 {model_id} 已存在"
        
        self.models.append({
            "id": model_id,
            "name": name,
            "description": description
        })
        self._save_models()
        return f"已添加模型: {name} ({model_id})"
    
    def remove_model(self, index: int) -> str:
        if 0 <= index < len(self.models):
            if len(self.models) == 1:
                return "至少保留一个模型"
            
            removed = self.models.pop(index)
            self._save_models()
            
            # 调整当前模型索引
            if self.model_index >= len(self.models):
                self.model_index = len(self.models) - 1
            
            return f"已删除模型: {removed['name']} ({removed['id']})"
        return f"无效编号，请输入 0-{len(self.models)-1}"
    
    def get_model_info(self) -> str:
        if not self.models:
            return "当前无模型"
        m = self.models[self.model_index]
        return f"当前模型: {m['name']} ({m['id']}) - {m['description']}"
    
    def chat(self, user_input: str) -> str:
        if not user_input.strip():
            return "请输入内容..."
        
        self.memory.add("user", user_input)
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": self.memory.get_messages(),
                    "temperature": 0.7
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            assistant_msg = result["choices"][0]["message"]["content"]
            self.memory.add("assistant", assistant_msg)
            return assistant_msg
            
        except Exception as e:
            return f"请求出错: {str(e)}"
    
    def get_history(self):
        return self.memory.get_history()
    
    def clear(self):
        self.memory.clear()
        return "已清空历史"
