from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int

    EVENTS_PROVIDER_BASE_URL: str = "http://events-provider.dev-2.python-labs.ru"
    EVENTS_PROVIDER_API_KEY: str = ""
    EVENTS_PROVIDER_TIMEOUT: float = 10.0

    WORKER_SYNC_INTERVAL: int = 24 * 60 * 60  # в секундах
    SEATS_CACHE_TIMEOUT: int = 30  # в секундах

    DEFAULT_PAGE_SIZE: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    @property
    def database_url(self):
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}"
            f":{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    # database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/events_aggregator"

    # events_provider_base_url: str = "http://events-provider.dev-2.python-labs.ru"
    # events_provider_api_key: str = ""
    # events_provider_timeout: float = 10.0

    # sync_interval_seconds: int = 24 * 60 * 60
    # seats_cache_ttl_seconds: int = 30

    # default_page_size: int = 20


settings = Settings()
