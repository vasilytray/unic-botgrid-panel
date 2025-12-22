# app/models/roles.py
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from app.models.users import User

from app.core.database import Base, int_pk, created_at, updated_at

class RoleTypes:
    """Типы ролей как константы"""
    SUPER_ADMIN = 1
    ADMIN = 2
    MODERATOR = 3
    USER = 4
    GUEST = 5

class Role(Base):
    # __tablename__ = "roles"
    
    id: Mapped[int_pk]
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    role_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    count_users: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="role")
    
    def __str__(self):
        return f"Role(id={self.id}, name={self.role_name}, users_count={self.count_users})"
    
    def __repr__(self):
        return str(self)
    
    @classmethod
    async def increment_count(cls, role_id: int):
        """Увеличить счетчик пользователей в роли"""
        from app.core.database import async_session_maker
        from sqlalchemy import update
        
        async with async_session_maker() as session:
            async with session.begin():
                stmt = update(cls).where(
                    cls.id == role_id
                ).values(count_users=cls.count_users + 1)
                await session.execute(stmt)
                await session.commit()
    
    @classmethod
    async def decrement_count(cls, role_id: int):
        """Уменьшить счетчик пользователей в роли"""
        from app.core.database import async_session_maker
        from sqlalchemy import update, and_
        
        async with async_session_maker() as session:
            async with session.begin():
                stmt = update(cls).where(
                    and_(cls.id == role_id, cls.count_users > 0)
                ).values(count_users=cls.count_users - 1)
                await session.execute(stmt)
                await session.commit()