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
    AI_CORE_API_KEY: str = os.getenv("AI_CORE_API_KEY", "QJ0Md2O3t8DMjT3jU1CwVAuOPoOkYZIp")
    AI_CORE_TIMEOUT: int = int(os.getenv("AI_CORE_TIMEOUT", 30))

    # LangFlow API
    LANGFLOW_API_URL: str = os.getenv("LANGFLOW_API_URL", "localhost:7860")
    LANGFLOW_API_KEY: str = os.getenv("LANGFLOW_API_KEY", "sdfsfsd")
    LANGFLOW_TIMEOUT: int = os.getenv("LANGFLOW_TIMEOUT", 420)
    LANGFLOW_JOB_OFFER_SUMMARY_GENERATION_FLOW_ID: str = os.getenv("LANGFLOW_JOB_OFFER_SUMMARY_GENERATION_FLOW_ID", "")
    LANGFLOW_JOB_OFFER_SKILLS_EXTRACTION_FLOW_ID: str= os.getenv("LANGFLOW_JOB_OFFER_SKILLS_EXTRACTION_FLOW_ID", "")
    LANGFLOW_CANDIDATE_SUMMARY_GENERATION_FLOW_ID: str = os.getenv("LANGFLOW_CANDIDATE_SUMMARY_GENERATION_FLOW_ID", "")
    LANGFLOW_CANDIDATE_SKILLS_EXTRACTION_FLOW_ID: str = os.getenv("LANGFLOW_CANDIDATE_SKILLS_EXTRACTION_FLOW_ID", "")
    LANGFLOW_CANDIDATE_ANONYMIZATION_API_FLOW_ID: str = os.getenv("LANGFLOW_CANDIDATE_ANONYMIZATION_API_FLOW_ID", "")
    LANGFLOW_JOB_OFFER_CANDIDATE_FIT_FLOW_ID: str = os.getenv("LANGFLOW_JOB_OFFER_CANDIDATE_FIT_FLOW_ID", "")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()