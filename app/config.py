from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator


class Settings(BaseSettings):
    DATABASE_URL: str
    GEMINI_API_KEY: str
    CORS_ORIGINS: str = "http://localhost:3000"

    @field_validator('CORS_ORIGINS')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle comma-separated values
            if ',' in v:
                return [origin.strip() for origin in v.split(',')]
            # Handle single value
            return [v.strip()]
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        return self.CORS_ORIGINS if isinstance(self.CORS_ORIGINS, list) else [self.CORS_ORIGINS]

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env file


settings = Settings()