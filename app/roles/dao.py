from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.dao.base import BaseDAO
from app.roles.models import Role, RoleTypes

class RolesDAO(BaseDAO):
    model = Role

    @classmethod
    async def find_all_with_users_count(cls, **filters):
        """Получить все роли (оптимизированно через BaseDAO)"""
        return await cls.find_all(**filters)

    @classmethod
    async def find_by_name(cls, role_name: str):
        """Найти роль по имени"""
        return await cls.find_one_or_none(role_name=role_name)
    
    @classmethod
    async def find_by_id(cls, role_id: int):
        """Найти роль по ID"""
        return await cls.find_one_or_none(id=role_id)

    @classmethod
    async def get_role_name_by_id(cls, role_id: int) -> str:
        """Получить название роли по ID"""
        role = await cls.find_by_id(role_id)
        return role.role_name if role else "Неизвестная роль"

    @classmethod
    async def get_available_roles(cls, exclude_super_admin: bool = False):
        """Получить список доступных ролей для назначения"""
        roles = await cls.find_all()
        if exclude_super_admin:
            roles = [role for role in roles if role.id != RoleTypes.SUPER_ADMIN]
        return roles

    @classmethod
    async def delete_role_by_name(cls, role_name: str) -> bool:
        """Удалить роль по имени (с проверкой на использование)"""
        # Находим роль
        role = await cls.find_by_name(role_name)
        if not role:
            return False
        
        # Проверяем, есть ли пользователи с этой ролью
        if role.count_users > 0:
            raise ValueError(f"Невозможно удалить роль '{role_name}'. Есть пользователи с этой ролью.")
        
        # Удаляем роль
        result = await cls.delete(role_name=role_name)
        return result > 0

    @classmethod
    async def get_role_stats(cls) -> dict:
        """Получить статистику по ролям"""
        roles = await cls.find_all()
        
        return {
            "total_roles": len(roles),
            "total_users": sum(role.count_users for role in roles),
            "roles": [
                {
                    "id": role.id,
                    "name": role.role_name,
                    "user_count": role.count_users,
                    "is_admin_role": role.is_admin_role
                }
                for role in roles
            ]
        }

    @classmethod
    async def get_admin_roles(cls):
        """Получить только административные роли"""
        roles = await cls.find_all()
        return [role for role in roles if role.is_admin_role]

    @classmethod
    async def update_role_description(cls, role_name: str, new_description: str) -> bool:
        """Обновить описание роли"""
        result = await cls.update(
            filter_by={'role_name': role_name},
            role_description=new_description
        )
        return result > 0