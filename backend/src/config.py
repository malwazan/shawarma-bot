import os
from enum import StrEnum

from logfire import LevelName
from pydantic import BaseModel, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    LOCAL = "local"
    PRODUCTION = "production"


class DatabaseSettings(BaseModel):
    dsn: str
    pool_size: int
    pool_recycle_seconds: int
    pool_pre_ping: bool


app_env = env = AppEnv(os.getenv("APP_ENV", AppEnv.LOCAL))
app_env_file = ".env"


class Settings(BaseSettings):
    APP_ENV: AppEnv = AppEnv.LOCAL
    DEBUG: bool = False
    SERVICE_NAME: str = "api"

    # DASEBASE
    MAIN_DB_USER: str = "admin"
    MAIN_DB_PASSWORD: str = "admintest"
    MAIN_DB_HOST: str = "localhost"
    MAIN_DB_PORT: int = 5432
    MAIN_DB_DATABASE: str = "postgres"
    MAIN_DB_POOL_SIZE: int = 5
    MAIN_DB_POOL_RECYCLE_SECONDS: int = 600
    MAIN_DB_POOL_PRE_PING: bool = False

    # LOGFIRE
    LOGFIRE_MIN_LEVEL: LevelName = "info"
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT: str = "http://localhost:4318/v1/traces"

    # AUTH
    AUTH_SECRET: SecretStr
    COOKIE_SECURE: bool = True

    # CORS
    CORS_ALLOWED_ORIGINS: list[str] = []

    # LIVEKIT
    LIVEKIT_URL: str = "ws://localhost:7880"  # Returned to the browser to join a room (wss://livekit.<domain> in production).
    LIVEKIT_API_URL: str = "http://localhost:7880"  # Used by the backend (room API) and the voice bot (http://livekit:7880 in production).
    LIVEKIT_API_KEY: str = "devkey"
    LIVEKIT_API_SECRET: SecretStr
    VOICE_AGENT_WS_URL: str = "ws://localhost:4001/api/v1/voice/livekit/call/connect"  # livekit bridge to voice agent. (ws://haproxy:4001/... in production, to spread calls over the workers).

    # MCP SERVER
    MCP_SERVER_URL: str = "http://localhost:4501/mcp"
    MCP_SERVER_SECRET: SecretStr = SecretStr("dev-mcp-secret")

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_file=app_env_file,
        extra="allow",
    )

    @property
    def main_db_settings(self) -> DatabaseSettings:
        return DatabaseSettings(
            dsn=str(
                PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=self.MAIN_DB_USER,
                    password=self.MAIN_DB_PASSWORD,
                    host=self.MAIN_DB_HOST,
                    port=self.MAIN_DB_PORT,
                    path=self.MAIN_DB_DATABASE,
                )
            ),
            pool_size=self.MAIN_DB_POOL_SIZE,
            pool_recycle_seconds=self.MAIN_DB_POOL_RECYCLE_SECONDS,
            pool_pre_ping=self.MAIN_DB_POOL_PRE_PING,
        )


settings = Settings()
