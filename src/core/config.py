from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    SENSITIVE_DATA: list[str] = [
        'password',
        'code',
    ]

    APP_NAME: str = 'NetVault'
    APP_VERSION: str = '0.1.0'
    APP_HOST: str = '0.0.0.0'
    APP_PORT: int = 8000
    DEBUG: bool = False

    EXTERNAL_ADDRESS: str
    SECURE: bool = False

    DEFAULT_STORAGE_QUOTA: int = 5 * 1024 * 1024 * 1024  # 5GB
    UPLOAD_THRESHOLD: int = 5 * 1024 * 1024  # 5MB
    UPLOAD_CHUNK_SIZE: int = 5 * 1024 * 1024  # 5MB

    MINIO_ENDPOINT: str
    MINIO_EXTERNAL_ENDPOINT: str | None = None
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: SecretStr
    MINIO_SECURE: bool = False

    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    SQLALCHEMY_ECHO: bool = False

    @property
    def POSTGRES_URL(self) -> str:
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    CACHE_TTL: int | None = 30
    AUTH_CACHE_TTL: int | None = 600

    @property
    def REDIS_URL(self) -> str:
        auth = f':{self.REDIS_PASSWORD}@' if self.REDIS_PASSWORD else ''
        return f'redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}'

    YC_POSTBOX_ACCESS_KEY: str
    YC_POSTBOX_SECRET_KEY: SecretStr
    YC_POSTBOX_REGION: str = 'ru-central1'
    YC_POSTBOX_ENDPOINT: str = 'https://postbox.cloud.yandex.net'

    MAIL_FROM: str

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    LOG_TO_FILE: bool = False
    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = '%(asctime)s | %(levelname)-8s | %(name)s | [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s'
    LOG_DATE_FORMAT: str = '%Y-%m-%d %H:%M:%S.%f'

    _LOGS_DIR: Path = BASE_DIR / 'logs'

    @property
    def LOGS_DIR(self) -> Path:
        Path.mkdir(self._LOGS_DIR, parents=True, exist_ok=True)
        return self._LOGS_DIR

    JWT_SECRET: SecretStr
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXP_MIN: int = 30
    REFRESH_TOKEN_EXP_MIN: int = 30 * 24 * 60


config = Config()
