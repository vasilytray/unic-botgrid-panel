from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import func, text
from typing import Annotated, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from loguru import logger

from app.core.config import get_settings
from app.core.exceptions import DatabaseConnectionException

# DATABASE_URL = get_db_url()
# Database engine and session
# engine = create_async_engine(get_settings().database_url) # создаёт асинхронное подключение к базе данных PostgreSQL, используя драйвер asyncpg
# async_session_maker = async_sessionmaker(engine, expire_on_commit=False) # создаёт фабрику асинхронных сессий, используя созданный движок. 
                                                                         # Сессии используются для выполнения транзакций в базе данных

# Database Manager класс для управления подключениями
class DatabaseManager:
    def __init__(self):
        self.settings = get_settings()
        self._engine = None  # приватные атрибуты
        self._async_session_maker = None
        self._initialized = False
    
    async def init_database(self):
        """Инициализация базы данных"""
        try:
            self._engine = create_async_engine(
                self.settings.database_url,
                echo=self.settings.DEBUG,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True
            )
            
            self._async_session_maker = async_sessionmaker(
                self._engine, 
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # ИНИЦИАЛИЗИРУЕМ ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
            global engine, async_session_maker
            engine = self._engine
            async_session_maker = self._async_session_maker
            
            self._initialized = True
            logger.info("✅ Database connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise DatabaseConnectionException(f"Database connection failed: {e}")
    @property
    def engine(self):
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        return self._engine
    
    @property
    def async_session_maker(self):
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        return self._async_session_maker
    
    async def close(self):
        """Закрытие подключений к БД"""
        if self._engine:
            await self._engine.dispose()
            self._initialized = False
            logger.info("✅ Database connections closed")
    
    async def health_check(self):
        """Проверка здоровья БД"""
        if not self._initialized or not self._engine:
            logger.error("Database not initialized")
            return False
            
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_session(self) -> AsyncSession:
        """Получить сессию БД"""
        if not self._initialized or not self._async_session_maker:
            raise DatabaseConnectionException("Database not initialized. Call init_database() first.")
        return self._async_session_maker()
    
    # Свойства для обратной совместимости
    @property
    def engine_compat(self):
        """Для обратной совместимости - получение engine"""
        if not self._initialized:
            raise DatabaseConnectionException("Database not initialized")
        return self._engine
    
    @property
    def async_session_maker_compat(self):
        """Для обратной совместимости - получение session maker"""
        if not self._initialized:
            raise DatabaseConnectionException("Database not initialized")
        return self._async_session_maker
    

# Глобальный экземпляр менеджера БД
database_manager = DatabaseManager()

# Функции для обратной совместимости (уровень модуля)
def get_engine():
    """
    Получить engine для обратной совместимости
    Старый импорт: from app.core.database import engine
    """
    if not database_manager._initialized:
        raise DatabaseConnectionException("Database not initialized. Call database_manager.init_database() first.")
    return database_manager._engine

def get_async_session_maker():
    """
    Получить async_session_maker для обратной совместимости
    Старый импорт: from app.core.database import async_session_maker
    """
    if not database_manager._initialized:
        raise DatabaseConnectionException("Database not initialized. Call database_manager.init_database() first.")
    return database_manager._async_session_maker

# Функция для dependency injection в FastAPI
async def get_db():
    """
    FastAPI dependency для получения сессии БД
    Использование: db: AsyncSession = Depends(get_db)
    """
    async with database_manager.get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Аннотации для моделей
int_pk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_null_true = Annotated[str, mapped_column(nullable=True)]

datetime_null_true = Annotated[Optional[datetime], mapped_column(nullable=True)]
bool_default_false = Annotated[bool, mapped_column(default=False)]
int_default_zero = Annotated[int, mapped_column(default=0)]
float_default_zero = Annotated[float, mapped_column(default=0.0)]

# Базовый класс для моделей
class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

# Глобальные переменные для обратной совместимости
# Они будут инициализированы после вызова database_manager.init_database()
# engine = None
# async_session_maker = None

# def init_compatibility_variables():
#     """
#     Инициализировать глобальные переменные для обратной совместимости
#     Должна быть вызвана после database_manager.init_database()
#     """
#     global engine, async_session_maker
#     engine = database_manager.engine
#     async_session_maker = database_manager.async_session_maker