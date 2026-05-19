# Centralizes MockAPI paths and configuration values.
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_DIR = f"{BASE_DIR}/.env"
TEMPLATES_DIR = f"{BASE_DIR}/ui/templates"
STATIC_DIR = f"{BASE_DIR}/ui/static"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = ENV_DIR,
        env_file_encoding = "utf-8",
        extra = "ignore",
    )

    app_name: str = "MockAPI"
    db_name: str = "mockapi.db"

    base_dir: Path = BASE_DIR
    env_dir: Path = ENV_DIR
    templates_dir: Path = TEMPLATES_DIR
    static_dir: Path = STATIC_DIR

    db_provider:str = "sqlite"

    @property
    def database_url(self) -> str:
        db_path = self.base_dir / self.db_name
        return f"{self.db_provider}:///{db_path}"
