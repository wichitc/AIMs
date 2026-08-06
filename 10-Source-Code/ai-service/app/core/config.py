from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://aims:aims@localhost:5432/aims"

    # Must match the Core API's signing config — this service validates, never issues, tokens.
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    anthropic_api_key: str | None = None
    llm_model: str = "claude-sonnet-5"
    embedding_dimensions: int = 1536

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
