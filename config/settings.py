from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:  # Python 3.10 compatibility
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for <3.11
    import tomli as tomllib  # type: ignore


CONFIG_PATH = Path(__file__).resolve().parent / "settings.toml"


class DeepSeekConfig(BaseModel):
    api_key: Optional[str] = Field(default=None, description="DeepSeek API key")
    model: str = Field(default="deepseek-reasoner", description="Default DeepSeek model")
    api_base: str = Field(default="https://api.deepseek.com/v1", description="Base URL for DeepSeek API")
    timeout_seconds: int = Field(default=60, description="Timeout for DeepSeek requests")


class RetrievalConfig(BaseModel):
    search_provider: Literal["duckduckgo", "tavily", "bing", "serpapi", "stub"] = Field(default="duckduckgo")
    tavily_api_key: Optional[str] = None
    bing_api_key: Optional[str] = None
    serpapi_key: Optional[str] = None
    wikipedia_language: str = Field(default="auto")
    max_documents: int = Field(default=10)
    bm25_k: float = Field(default=1.2)
    bm25_b: float = Field(default=0.75)


class StorageConfig(BaseModel):
    persist_directory: str = Field(default=".chromadb")
    reset_on_startup: bool = Field(default=False)


class AppConfig(BaseModel):
    locale: str = Field(default="auto")
    default_language: str = Field(default="auto")
    enable_streamlit: bool = Field(default=True)


class LangsmithConfig(BaseModel):
    enabled: bool = Field(default=False)
    api_key: Optional[str] = None
    api_url: str = Field(default="https://api.smith.langchain.com")
    project: str = Field(default="FakeScope")


class FakeScopeSettings(BaseSettings):
    deepseek: DeepSeekConfig = Field(default_factory=DeepSeekConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    langsmith: LangsmithConfig = Field(default_factory=LangsmithConfig)

    model_config = SettingsConfigDict(env_prefix="FAKESCOPE_", env_nested_delimiter="__", extra="ignore")

    @classmethod
    def from_file(cls, path: Path = CONFIG_PATH) -> "FakeScopeSettings":
        if path.exists():
            with path.open("rb") as fh:
                data = tomllib.load(fh)
            return cls.model_validate(data)
        return cls()


@lru_cache(maxsize=1)
def get_settings() -> FakeScopeSettings:
    """Return a cached application settings instance."""

    env_override = FakeScopeSettings()
    file_settings = FakeScopeSettings.from_file()

    return file_settings.model_copy(update=env_override.model_dump(exclude_unset=True))


__all__ = [
    "FakeScopeSettings",
    "DeepSeekConfig",
    "RetrievalConfig",
    "StorageConfig",
    "AppConfig",
    "LangsmithConfig",
    "get_settings",
]

