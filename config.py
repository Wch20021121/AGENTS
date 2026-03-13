import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")
MODELS_PATH = os.getenv("MODELS_PATH", "config/models.txt")

def validate_config() -> None:
    if not API_KEY:
        raise ValueError("请在 .env 文件中配置 API_KEY")
    if not BASE_URL:
        raise ValueError("请在 .env 文件中配置 BASE_URL")
    if not Path(MODELS_PATH).exists():
        raise ValueError(f"模型配置文件不存在: {MODELS_PATH}")