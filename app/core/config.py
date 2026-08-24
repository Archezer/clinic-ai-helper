from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    openrouter_api_key: SecretStr
    openrouter_model: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    rag_document_path: str = "output/pdf/clinic_faq_rag_demo.pdf"
    rag_top_k: int = 4
    rag_min_score: float = 0.12
    messenger_mode: Literal["meta", "fake"] = "meta"
    enable_dev_routes: bool = False

    database_url: SecretStr
    meta_verify_token: SecretStr | None = None
    meta_app_secret: SecretStr | None = None
    meta_page_access_token: SecretStr | None = None
    meta_graph_base_url: str = "https://graph.facebook.com"
    meta_graph_api_version: str = "v23.0"
    admin_api_token: SecretStr | None = None
    cors_allowed_origins: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
