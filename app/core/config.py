import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
   
    # Redis (для кэширования)
    REDIS_URL: str
    REDIS_PASSWORD: str
    REDIS_DB: int = 0
    REDIS_USER: str
    REDIS_USER_PASSWORD: str
    REDIS_HOST: str = "redis_container"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    
    # Centrifugo
    CENTRIFUGO_URL: str = "http://localhost:8000"
    CENTRIFUGO_API_KEY: Optional[str] = None
    CENTRIFUGO_SECRET_KEY: Optional[str] = None
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"),
        extra='ignore'  # ← ИГНОРИРОВАТЬ ЛИШНИЕ ПЕРЕМЕННЫЕ
    )

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def redis_connection_url(self) -> str:
        return f"redis://{self.REDIS_USER}:{self.REDIS_USER_PASSWORD}@{self.REDIS_HOST}:6379/{self.REDIS_DB}"


settings = Settings() # type: ignore


# def get_db_url():
#     return (f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
#             f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

# def get_auth_data():
#     return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}