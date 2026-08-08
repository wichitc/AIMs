from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://aims:aims@localhost:5432/aims"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Comma-separated list of allowed frontend origins (SecurityTest.md SEC-016).
    # Defaults to local dev only — never "*" — so production must set this explicitly.
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # API-Spec.md originally specified a pre-signed-URL flow (client uploads directly to
    # object storage, API only registers metadata) — no object storage service exists in
    # this deployment yet (no MinIO/S3 in docker-compose.yml), so documents are stored on
    # a local volume behind the API instead. Swap this for real object storage + presigned
    # URLs before scaling past a single backend replica (local disk doesn't share across
    # instances).
    document_storage_path: str = "/app/storage/documents"


settings = Settings()
