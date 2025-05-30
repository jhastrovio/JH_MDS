# backend/core/settings.py
from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field


class Settings(BaseSettings):
    ENV: str = Field("development", env="ENV")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    REDIS_URL: AnyUrl = Field(..., env="REDIS_URL")
    REDIS_POOL_SIZE: int = Field(10, env="REDIS_POOL_SIZE")
    SAXO_APP_KEY: str = Field("", env="SAXO_APP_KEY")
    SAXO_SECRET: str = Field("", env="SAXO_APP_SECRET")
    SAXO_REDIRECT_URI: str = Field("http://localhost:8000/callback", env="SAXO_REDIRECT_URI")
    FRONTEND_URL: Optional[AnyUrl] = Field(None, env="FRONTEND_URL")
    VERCEL: bool = Field(False, env="VERCEL")
    HTTP_TIMEOUT: float = Field(10.0, env="HTTP_TIMEOUT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_cors_origins(self) -> List[str]:
        origins = [
            "https://jh-mds-frontend.vercel.app",
        ]
        if self.VERCEL:
            origins += [
                "https://*.vercel.app",
                "https://jh-mds-frontend-*.vercel.app",
            ]
        else:
            origins += [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
        if self.FRONTEND_URL:
            origins.append(str(self.FRONTEND_URL))
        return origins

    def is_saxo_configured(self) -> bool:
        """Check if Saxo Bank credentials are properly configured."""
        return bool(self.SAXO_APP_KEY and self.SAXO_SECRET and self.SAXO_REDIRECT_URI)


@lru_cache()
def get_settings() -> Settings:
    return Settings()

