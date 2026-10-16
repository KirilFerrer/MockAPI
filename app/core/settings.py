"""Local configuration for the HTTP mock server and its web UI."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # The local .env file is app/.env, beside the application package.
    model_config = SettingsConfigDict(
        env_file=APP_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "mockAPI"
    db_name: str = "mockapi.db"
    cors_origins: list[str] = []

    base_dir: Path = APP_DIR
    templates_dir: Path = APP_DIR / "ui" / "templates"
    static_dir: Path = APP_DIR / "ui" / "static"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.base_dir / self.db_name}"
