#/app/core/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache



class Settings(BaseSettings):
    # Database - значения по умолчанию только для разработки
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "botgrid_db"
    DB_USER: str = "postgres"  # Безопасное значение по умолчанию
    DB_PASSWORD: str = "postgres"  # Безопасное значение по умолчанию
    
    # JWT - БЕЗ значений по умолчанию для безопасности!
    SECRET_KEY: str  # Required variable
    ALGORITHM: str = "HS256"  # Значение по умолчанию безопасно
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
   
    # Redis (для кэширования)
    REDIS_URL: str
    REDIS_PASSWORD: str
    REDIS_DB: int = 0
    REDIS_USER: str
    REDIS_USER_PASSWORD: str
    REDIS_HOST: str = "redis_container"
    REDIS_PORT: int = 6379 

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    
    # Centrifugo
    CENTRIFUGO_URL: str = "http://localhost:8000"
    CENTRIFUGO_API_KEY: Optional[str] = None
    CENTRIFUGO_SECRET_KEY: Optional[str] = "123545"
    
    # Application
    app_name: str = "BotGrid Hosting Panel"
    ENVIRONMENT: str = "development"   # development/staging/production
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Security
    bcrypt_rounds: int = 12

    model_config = SettingsConfigDict(
        # Ищем .env файл в корне проекта (рядом с docker-compose.yml)
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,  # Регистронезависимые переменные
        extra="ignore"  # Игнорировать лишние переменные
    )

    @property
    def database_url(self) -> str:
        """URL для подключения к PostgreSQL"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def redis_connection_url(self) -> str:
        """URL для подключения к Redis"""
        if self.REDIS_USER and self.REDIS_USER_PASSWORD:
            # Production: redis://user:password@host:port/db
            return f"redis://{self.REDIS_USER}:{self.REDIS_USER_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        elif self.REDIS_PASSWORD:
            # Стандартный способ: redis://:password@host:port/db
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            # Локальная разработка без пароля
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def is_production(self) -> bool:
        """Проверка production окружения"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Проверка development окружения"""
        return self.ENVIRONMENT == "development"

@lru_cache()
def get_settings() -> Settings:
    """
    Получить настройки (кэшируется)
    
    Приоритет загрузки настроек:
    1. Переменные окружения системы
    2. .env файл
    3. Значения по умолчанию из класса
    """
    try:
        settings = Settings() # type: ignore
        
        # Валидация для production
        if settings.is_production:
            if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here":
                raise ValueError("SECRET_KEY must be set in production environment")
            
            if not settings.CENTRIFUGO_API_KEY or not settings.CENTRIFUGO_SECRET_KEY:
                raise ValueError("Centrifugo API keys must be set in production environment")
        
        return settings
        
    except Exception as e:
        # Логируем ошибку загрузки конфигурации
        import logging
        logging.error(f"Failed to load settings: {e}")
        raise


# Для обратной совместимости
def get_db_url() -> str:
    """Старая функция для обратной совместимости"""
    return get_settings().database_url

def get_auth_data() -> dict:
    """Старая функция для обратной совместимости"""
    settings = get_settings()
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}

def get_auth_cent_data() -> dict:
    """Старая функция для обратной совместимости"""
    settings = get_settings()
    return {"secret_key": settings.CENTRIFUGO_SECRET_KEY, "algorithm": settings.ALGORITHM}

# def get_db_url():
#     return (f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
#             f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

# def get_auth_data():
#     return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}