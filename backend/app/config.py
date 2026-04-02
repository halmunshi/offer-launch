from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import certifi

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_URL_DIRECT: str
    FRONTEND_URL: str
    CLERK_WEBHOOK_SECRET: str
    CLERK_JWKS_URL: str | None = None
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    ENVIRONMENT: str = "development"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        database_url = value

        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

        split_url = urlsplit(database_url)
        query_params = parse_qsl(split_url.query, keep_blank_values=True)
        rewritten_query: list[tuple[str, str]] = []

        for key, param_value in query_params:
            if key == "sslmode":
                rewritten_query.append(("ssl", "require" if param_value != "disable" else "disable"))
                continue
            if key == "channel_binding":
                continue
            rewritten_query.append((key, param_value))

        return urlunsplit(
            (
                split_url.scheme,
                split_url.netloc,
                split_url.path,
                urlencode(rewritten_query),
                split_url.fragment,
            )
        )

    @field_validator("DATABASE_URL_DIRECT", mode="before")
    @classmethod
    def normalize_database_url_direct(cls, value: str) -> str:
        direct_url = value
        if direct_url.startswith("postgresql+asyncpg://"):
            return direct_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        if direct_url.startswith("postgres://"):
            return direct_url.replace("postgres://", "postgresql://", 1)
        return direct_url

    @field_validator("REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def normalize_redis_tls_url(cls, value: str) -> str:
        redis_url = value.strip()
        split_url = urlsplit(redis_url)

        if split_url.scheme != "rediss":
            return redis_url

        query_params = parse_qsl(split_url.query, keep_blank_values=True)
        params = {key: param_value for key, param_value in query_params}

        params["ssl_cert_reqs"] = "required"
        params.setdefault("ssl_ca_certs", certifi.where())

        return urlunsplit(
            (
                split_url.scheme,
                split_url.netloc,
                split_url.path,
                urlencode(list(params.items())),
                split_url.fragment,
            )
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
