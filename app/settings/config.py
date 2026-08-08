from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    name: str
    url: str


class ProviderSeettings(BaseModel):
    base_url: str = ''
    api_key: str = ''
    timeout: float = 10.0


class CapashinoSettings(BaseModel):
    base_url: str
    api_key: str


class Settings(BaseSettings):
    POSTGRES_DATABASE_NAME: str
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    EVENTS_PROVIDER_BASE_URL: str = ''
    EVENTS_PROVIDER_API_KEY: str = ''
    EVENTS_PROVIDER_TIMEOUT: float = 10.0
    WORKER_SYNC_INTERVAL: int = 24 * 60 * 60  # в секундах
    SEATS_CACHE_TIMEOUT: int = 30  # в секундах
    DEFAULT_PAGE_SIZE: int = 20
    CAPASHINO_BASE_URL: str = ''
    CAPASHINO_API_KEY: str = ''
    OUTBOX_DISPATCH_INTERVAL: int = 30  # в секундах
    OUTBOX_MAX_ATTEMPTS: int = 5
    OUTBOX_LIMIT_ROWS: int = 50
    GLITCHTIP_DSN: str = ''


    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='',
        extra='ignore',
    )

    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings(
            name=self.POSTGRES_DATABASE_NAME,
            url=(
                f'postgresql+asyncpg://{self.POSTGRES_USERNAME}'
                f':{self.POSTGRES_PASSWORD}'
                f'@{self.POSTGRES_HOST}'
                f':{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE_NAME}'
            )
        )

    @property
    def provider(self) -> ProviderSeettings:
        return DatabaseSettings(
            base_url=self.EVENTS_PROVIDER_BASE_URL,
            api_key=self.EVENTS_PROVIDER_API_KEY,
            timeout=self.EVENTS_PROVIDER_TIMEOUT
        )

    @property
    def capashino(self) -> CapashinoSettings:
        return CapashinoSettings(
            base_url=self.CAPASHINO_BASE_URL,
            api_key=self.CAPASHINO_API_KEY
        )


settings = Settings()
