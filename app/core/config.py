"""Application configuration using Pydantic Settings"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "KrishiMitra"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/krishimitra"

    # API Keys
    openai_api_key: Optional[str] = None

    # Voice Services
    google_cloud_speech_key_path: Optional[str] = None

    # Demo Farmer Context (Hackathon)
    demo_farmer_id: str = "farmer_001"
    demo_farmer_name: str = "राज किसान"
    demo_farmer_language: str = "marathi"
    demo_farmer_state: str = "maharashtra"
    demo_farmer_budget: int = 50000
    demo_farmer_land_size: float = 2.0

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
