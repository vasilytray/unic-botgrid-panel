from datetime import datetime
from typing import Annotated, Optional

from sqlalchemy import func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column

from app.config import get_db_url


DATABASE_URL = get_db_url()

engine = create_async_engine(DATABASE_URL) # создаёт асинхронное подключение к базе данных PostgreSQL, используя драйвер asyncpg
async_session_maker = async_sessionmaker(engine, expire_on_commit=False) # создаёт фабрику асинхронных сессий, используя созданный движок. 
                                                                         # Сессии используются для выполнения транзакций в базе данных

# настройка аннотаций
int_pk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_null_true = Annotated[str, mapped_column(nullable=True)]

datetime_null_true = Annotated[Optional[datetime], mapped_column(nullable=True)]
bool_default_false = Annotated[bool, mapped_column(default=False)]
int_default_zero = Annotated[int, mapped_column(default=0)]
float_default_zero = Annotated[float, mapped_column(default=0.0)]

# абстрактный класс, от которого наследуются все модели.
class Base(AsyncAttrs, DeclarativeBase): 
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]