from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/news.db"

    # Gemini API
    google_api_key: str = ""

    # AI 설정
    ai_model: str = "gemini-2.0-flash"
    ai_max_tokens: int = 500
    ai_batch_size: int = 10

    # 수집 설정
    collect_interval_minutes: int = 60
    max_news_per_source: int = 50

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
