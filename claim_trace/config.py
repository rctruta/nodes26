"""Machine-specific settings, loaded from `.env` and validated on start."""
from pathlib import Path

from pydantic import PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    neo4j_password: SecretStr
    neo4j_host: str
    neo4j_image: str
    base_http_port: PositiveInt
    base_bolt_port: PositiveInt
    results_dir: Path
    compose_project_prefix: str
    log_level: str
    openai_api_key: SecretStr | None = None

    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    @property
    def results_path(self) -> Path:
        return self.results_dir if self.results_dir.is_absolute() else ROOT / self.results_dir
