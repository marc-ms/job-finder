from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite:///./data/jobs.db"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-4-hydrogen"
    GEMINI_THINKING_LEVEL: str = "xhigh"
    APP_PASSWORD: str = ""


settings = Settings()


def load_filters(path: Path | None = None) -> dict[str, Any]:
    filters_path = path or (CONFIG_DIR / "filters.yaml")
    with filters_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data if isinstance(data, dict) else {}


def load_profile(path: Path | None = None) -> str:
    profile_path = path or (CONFIG_DIR / "profile.md")
    return profile_path.read_text(encoding="utf-8").strip()
