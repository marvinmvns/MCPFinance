from __future__ import annotations

from functools import lru_cache
import json
from typing import List

from pydantic import AnyUrl, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "clean-api"
    ENV: str = Field(default="local")

    API_PREFIX: str = "/v1"
    OPENAPI_TITLE: str = "clean-api"
    OPENAPI_VERSION: str = "1.0.0"

    DB_DSN: str = Field(
        default="sqlite+aiosqlite:///./.local.sqlite", description="SQLAlchemy async DSN"
    )

    JWT_SECRET: str = Field(default="change-me")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_AUDIENCE: str = Field(default="clean-api")
    JWT_ISSUER: str = Field(default="clean-api")
    JWT_EXPIRE_SECONDS: int = Field(default=3600)

    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None
    PROMETHEUS_PORT: int = 9000

    # Raw env value; parsed via property to avoid env JSON parsing errors
    CORS_ORIGINS_RAW: str | None = None

    # Feature toggles
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = False


class OpenAPIContact(BaseModel):
    name: str = "Maintainers"
    url: AnyUrl | None = None
    email: str | None = None


@lru_cache(1)
def get_settings() -> Settings:
    return Settings()

    
@property
def _cors_default() -> List[str]:  # helper for default origins
    return ["*"]


# Add a computed property on Settings to expose parsed CORS origins
def _parse_cors(origins_raw: str | None) -> List[str]:
    if not origins_raw:
        return ["*"]
    value = origins_raw.strip()
    if value == "*":
        return ["*"]
    # JSON array
    if value.startswith("[") and value.endswith("]"):
        try:
            data = json.loads(value)
            if isinstance(data, list):
                return [str(v) for v in data]
        except json.JSONDecodeError:
            pass
    # Comma-separated
    if "," in value:
        return [v.strip() for v in value.split(",") if v.strip()]
    # Single origin string
    return [value]


# monkey-patch property onto Settings class to keep existing access pattern
def _get_cors(self: Settings) -> List[str]:
    return _parse_cors(self.CORS_ORIGINS_RAW)


Settings.CORS_ORIGINS = property(_get_cors)  # type: ignore[attr-defined]
