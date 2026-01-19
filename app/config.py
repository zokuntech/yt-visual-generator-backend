"""
Application configuration
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    openai_api_key: str
    google_gemini_api_key: str
    google_docs_credentials_path: Optional[str] = None
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # App settings
    app_name: str = "YT Visual Generator API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"Warning: Could not load settings: {e}")
    print("Make sure you have a .env file with required variables")
    settings = None
