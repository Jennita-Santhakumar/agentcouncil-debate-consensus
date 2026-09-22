from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "ollama"
    ollama_model: str = "llama3.2:3b"
    ollama_base_url: str = "http://host.docker.internal:11434"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-haiku-latest"

    database_url: str = "postgresql+psycopg://debate:debate@localhost:5512/debate"
    cors_origins: str = "http://localhost:5300"

    max_search_results: int = 4
    default_num_rounds: int = 3

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
