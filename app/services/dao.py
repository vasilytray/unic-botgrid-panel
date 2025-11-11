# app/services/dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import List, Dict, Any, Optional

from app.database import async_session_maker
from app.services.models import Service, ServiceStatus

class ServicesDAO:
    model = Service

    @classmethod
    async def get_user_services(cls, user_id: int) -> List[Service]:
        """Получить все сервисы пользователя с загрузкой пользователя"""
        async with async_session_maker() as session:
            query = (select(cls.model)
                    .options(joinedload(cls.model.user))
                    .filter_by(user_id=user_id)
                    .order_by(cls.model.created_at.desc()))
            result = await session.execute(query)
            return result.unique().scalars().all()

    @classmethod
    async def get_user_service_stats(cls, user_id: int) -> Dict[str, Any]:
        """Получить статистику сервисов пользователя"""
        async with async_session_maker() as session:
            # Количество сервисов по типам
            query = (select(cls.model.service_type, func.count(cls.model.id))
                    .filter_by(user_id=user_id)
                    .group_by(cls.model.service_type))
            result = await session.execute(query)
            type_stats = dict(result.all())
            
            # Количество сервисов по статусам
            status_query = (select(cls.model.status, func.count(cls.model.id))
                          .filter_by(user_id=user_id)
                          .group_by(cls.model.status))
            status_result = await session.execute(status_query)
            status_stats = dict(status_result.all())
            
            return {
                "by_type": type_stats,
                "by_status": status_stats
            }

    @classmethod
    async def get_service_with_user(cls, service_id: int) -> Optional[Service]:
        """Получить сервис с информацией о пользователе"""
        async with async_session_maker() as session:
            query = (select(cls.model)
                    .options(joinedload(cls.model.user))
                    .filter_by(id=service_id))
            result = await session.execute(query)
            return result.unique().scalar_one_or_none()