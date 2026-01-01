from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/news.db"

    # Gemini API (comma-separated for multiple keys)
    google_api_keys: str = ""  # Multiple keys: "key1,key2,key3"
    google_api_key: str = ""   # Single key (legacy support)

    # Naver API (https://developers.naver.com)
    naver_client_id: str = ""
    naver_client_secret: str = ""

    # AI 설정
    ai_model: str = "gemini-2.0-flash"
    ai_max_tokens: int = 500
    ai_batch_size: int = 10
    ai_daily_limit_per_key: int = 1500  # Gemini Flash free tier

    def get_api_keys(self) -> list[str]:
        """Get list of valid API keys"""
        keys = []
        # First add keys from google_api_keys (comma-separated)
        if self.google_api_keys:
            keys.extend([k.strip() for k in self.google_api_keys.split(',') if k.strip()])
        # Then add single key if not already in list
        if self.google_api_key and self.google_api_key not in keys:
            keys.append(self.google_api_key)
        return keys

    def has_naver_api(self) -> bool:
        """Check if Naver API is configured"""
        return bool(self.naver_client_id and self.naver_client_secret)

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True


def get_settings() -> Settings:
    """Get settings (no cache for development)"""
    return Settings()
