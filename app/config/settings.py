from pathlib import Path
from typing import Optional


class Settings:
    """Application settings and configuration"""
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:246659@100.97.74.126:5432/postgres"
    
    # File Upload
    BASE_UPLOAD_DIR: Path = Path("/Volumes/server-storage/whatthedog/Dogs image")
    MAX_BYTES: int = 8 * 1024 * 1024  # 8 MB limit
    
    # API
    API_TITLE: str = "Photo Receiver API"
    API_VERSION: str = "1.0.0"
    
    # CORS
    CORS_ORIGINS: list = ["*"]  # Allow all origins - restrict in production
    
    def __init__(self):
        # Ensure upload directory exists
        self.BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
