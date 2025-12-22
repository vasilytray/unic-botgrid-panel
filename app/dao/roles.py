# app/dao/roles.py
from sqlalchemy import select
from typing import Optional, List, Sequence
from app.core.database import database_manager
from app.dao.base import BaseDAO
from app.models.roles import Role, RoleTypes
from app.schemas.roles import RoleResponse, RoleSimpleResponse

class RoleDAO(BaseDAO):
    model = Role

    async def find_all_with_users_count(self, **filters) -> List[Role]:
        """Получить все роли с подсчетом пользователей"""
        roles = await self.find_all(**filters)
        return list(roles)  # Явное преобразование Sequence[Role] -> List[Role]

    async def find_by_name(self, role_name: str) -> Optional[Role]:
        """Найти роль по имени"""
        return await self.find_one_or_none(role_name=role_name)
    
    async def find_by_id(self, role_id: int) -> Optional[Role]:
        """Найти роль по ID"""
        return await self.find_one_or_none(id=role_id)

    async def get_role_name_by_id(self, role_id: int) -> str:
        """Получить название роли по ID"""
        role = await self.find_by_id(role_id)
        return role.role_name if role else "Неизвестная роль"

    async def get_available_roles(self, exclude_super_admin: bool = False) -> List[Role]:
        """Получить список доступных ролей для назначения"""
        async with database_manager.get_session() as session:
            query = select(self.model)
            if exclude_super_admin:
                query = query.where(self.model.id != RoleTypes.SUPER_ADMIN)
            
            result = await session.execute(query)
            roles: Sequence[Role] = result.scalars().all()
            return list(roles)  # Явное преобразование

    async def delete_role_by_name(self, role_name: str) -> bool:
        """Удалить роль по имени (с проверкой на использование)"""
        role = await self.find_by_name(role_name)
        if not role:
            return False
        
        if role.count_users > 0:
            raise ValueError(f"Невозможно удалить роль '{role_name}'. Есть пользователи с этой ролью.")
        
        result = await self.delete(role_name=role_name)
        return result > 0

    async def get_role_stats(self) -> dict:
        """Получить статистику по ролям"""
        roles = await self.find_all()
        role_list = list(roles)  # Преобразуем Sequence в List
        
        return {
            "total_roles": len(role_list),
            "total_users": sum(role.count_users for role in role_list),
            "roles": [
                {
                    "id": role.id,
                    "name": role.role_name,
                    "user_count": role.count_users,
                    "is_admin_role": role.is_admin_role
                }
                for role in role_list
            ]
        }

    async def get_admin_roles(self) -> List[Role]:
        """Получить только административные роли"""
        roles = await self.find_all()
        role_list = list(roles)  # Преобразуем Sequence в List
        return [role for role in role_list if role.is_admin_role]

    async def update_role_description(self, role_name: str, new_description: str) -> bool:
        """Обновить описание роли"""
        result = await self.update(
            filter_by={'role_name': role_name},
            role_description=new_description
        )
        return result > 0

    async def create_role(self, role_name: str, role_description: Optional[str] = None) -> Role:
        """Создать новую роль"""
        # Обрабатываем Optional параметр
        data = {"role_name": role_name}
        if role_description is not None:
            data["role_description"] = role_description
            
        return await self.add(**data)

    async def update_role_data(self, role_id: int, **update_data) -> bool:
        """Обновить данные роли"""
        excluded_fields = {'id', 'created_at', 'updated_at'}
        filtered_data = {
            k: v for k, v in update_data.items() 
            if k not in excluded_fields and v is not None
        }
        
        if not filtered_data:
            return False
            
        result = await self.update(
            filter_by={'id': role_id},
            **filtered_data
        )
        return result > 0

    async def get_all_roles_as_response(self) -> List[RoleResponse]:
        """Получить все роли в виде схем ответа"""
        roles = await self.get_all_roles()
        return [
            RoleResponse(
                id=role.id,
                role_name=role.role_name,
                role_description=role.role_description,
                count_users=role.count_users,
                created_at=role.created_at,
                updated_at=role.updated_at
            )
            for role in roles
        ]

    # Альтернативные методы для совместимости
    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Найти роль по ID (альтернативное название)"""
        return await self.find_by_id(role_id)

    async def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """Найти роль по имени (альтернативное название)"""
        return await self.find_by_name(role_name)

    async def get_all_roles(self) -> List[Role]:
        """Получить все роли (альтернативное название)"""
        roles = await self.find_all()
        return list(roles)

    async def get_role_users_count(self, role_id: int) -> int:
        """Получить количество пользователей с данной ролью"""
        role = await self.find_by_id(role_id)
        return role.count_users if role else 0