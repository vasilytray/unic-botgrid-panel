from sqlalchemy import select, delete, and_
from sqlalchemy.orm import joinedload
from app.dao.base import BaseDAO
from app.users.models import UserAllowedIP
from app.database import async_session_maker
from typing import List, Optional

class UserAllowedIPsDAO(BaseDAO):
    model = UserAllowedIP

    @classmethod
    async def find_by_user_id(cls, user_id: int, active_only: bool = True) -> List[UserAllowedIP]:
        """Найти все разрешенные IP для пользователя"""
        filters = {'user_id': user_id}
        if active_only:
            filters['is_active'] = 1
        
        return await cls.find_all(**filters)

    @classmethod
    async def find_by_ip_and_user(cls, user_id: int, ip_address: str) -> Optional[UserAllowedIP]:
        """Найти конкретный IP адрес для пользователя"""
        return await cls.find_one_or_none(user_id=user_id, ip_address=ip_address)

    @classmethod
    async def add_ip_for_user(cls, user_id: int, ip_address: str, description: str = None) -> UserAllowedIP:
        """Добавить IP адрес для пользователя"""
        # Проверяем, не существует ли уже этот IP
        existing = await cls.find_by_ip_and_user(user_id, ip_address)
        if existing:
            # Если существует но не активен - активируем
            if not existing.is_active:
                await cls.update(
                    filter_by={'id': existing.id},
                    is_active=1,
                    description=description
                )
                return existing
            return existing
        
        # Создаем новый
        return await cls.add(
            user_id=user_id,
            ip_address=ip_address,
            description=description
        )

    @classmethod
    async def add_multiple_ips(cls, user_id: int, ip_addresses: List[str]) -> List[UserAllowedIP]:
        """Добавить несколько IP адресов для пользователя"""
        results = []
        for ip in ip_addresses:
            ip_record = await cls.add_ip_for_user(user_id, ip)
            results.append(ip_record)
        return results

    @classmethod
    async def deactivate_ip(cls, user_id: int, ip_address: str) -> bool:
        """Деактивировать IP адрес (мягкое удаление)"""
        ip_record = await cls.find_by_ip_and_user(user_id, ip_address)
        if not ip_record:
            return False
        
        result = await cls.update(
            filter_by={'id': ip_record.id},
            is_active=0
        )
        return result > 0

    @classmethod
    async def delete_ip(cls, user_id: int, ip_address: str) -> bool:
        """Полностью удалить IP адрес"""
        ip_record = await cls.find_by_ip_and_user(user_id, ip_address)
        if not ip_record:
            return False
        
        result = await cls.delete(id=ip_record.id)
        return result > 0

    @classmethod
    async def delete_all_user_ips(cls, user_id: int) -> bool:
        """Удалить все IP адреса пользователя"""
        result = await cls.delete(user_id=user_id)
        return result > 0

    @classmethod
    async def is_ip_allowed(cls, user_id: int, ip_address: str) -> bool:
        """Проверить, разрешен ли IP адрес для пользователя"""
        ip_record = await cls.find_one_or_none(
            user_id=user_id,
            ip_address=ip_address,
            is_active=1
        )
        return ip_record is not None

    @classmethod
    async def get_user_allowed_ips_list(cls, user_id: int) -> List[str]:
        """Получить список разрешенных IP адресов пользователя"""
        ip_records = await cls.find_by_user_id(user_id, active_only=True)
        return [ip.ip_address for ip in ip_records]

    @classmethod
    async def update_ip_description(cls, user_id: int, ip_address: str, description: str) -> bool:
        """Обновить описание IP адреса"""
        ip_record = await cls.find_by_ip_and_user(user_id, ip_address)
        if not ip_record:
            return False
        
        result = await cls.update(
            filter_by={'id': ip_record.id},
            description=description
        )
        return result > 0