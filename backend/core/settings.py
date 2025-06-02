# backend/core/settings.py
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field
import os


class Settings(BaseSettings):
    ENV: str = Field("development", env="ENV")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    REDIS_URL: AnyUrl = Field(..., env="REDIS_URL")
    REDIS_POOL_SIZE: int = Field(10, env="REDIS_POOL_SIZE")
    SAXO_APP_KEY: str = Field("", env="SAXO_APP_KEY")
    SAXO_APP_SECRET: str = Field("", env="SAXO_APP_SECRET")
    SAXO_REDIRECT_URI: str = Field("http://localhost:8000/callback", env="SAXO_REDIRECT_URI")
    NEXT_PUBLIC_API_URL: Optional[AnyUrl] = Field(None, env="NEXT_PUBLIC_API_URL")
    VERCEL: bool = Field(False, env="VERCEL")
    # If EXTERNAL_API_URL isn't set, it should fall back to NEXT_PUBLIC_API_URL
    EXTERNAL_API_URL: Optional[AnyUrl] = Field(None, env="EXTERNAL_API_URL")
    FRONTEND_URL: Optional[AnyUrl] = Field(None, env="NEXT_PUBLIC_API_URL")
    HTTP_TIMEOUT: float = Field(10.0, env="HTTP_TIMEOUT")
    JWT_SECRET: str = Field(..., env="JWT_SECRET")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def model_post_init(self, __context) -> None:
        """
        After model initialization, ensure settings have appropriate fallbacks.
        This runs after Pydantic loads the settings from environment variables.
        """
        # Use NEXT_PUBLIC_API_URL as a fallback for EXTERNAL_API_URL
        if not self.EXTERNAL_API_URL and self.NEXT_PUBLIC_API_URL:
            # Pydantic doesn't allow direct assignment to fields after initialization
            # so we use object.__setattr__ to bypass validation
            object.__setattr__(self, "EXTERNAL_API_URL", self.NEXT_PUBLIC_API_URL)
    
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
        next_public_api_url = os.getenv("NEXT_PUBLIC_API_URL")
        if next_public_api_url:
            origins.append(next_public_api_url)
        return origins

    def is_saxo_configured(self) -> bool:
        """Check if Saxo Bank credentials are properly configured."""
        return bool(self.SAXO_APP_KEY and self.SAXO_APP_SECRET and self.SAXO_REDIRECT_URI)


def get_settings() -> Settings:
    return Settings()

