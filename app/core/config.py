# core/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Dashboard Generator"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = ""    
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", 30))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", 60))
    DATABASE_POOL_TIMEOUT: int = int(os.getenv("DATABASE_POOL_TIMEOUT", 60))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", 3600))

    # AI Core
    AI_CORE_URL: str = os.getenv("AI_CORE_URL", "http://localhost:8000")
    AI_CORE_API_KEY: str = os.getenv("AI_CORE_API_KEY", "123456789")
    AI_CORE_TIMEOUT: int = int(os.getenv("AI_CORE_TIMEOUT", 30))

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()