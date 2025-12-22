# app/dao/users.py
from sqlalchemy import select, update, desc, or_
from sqlalchemy.orm import joinedload
from typing import Optional, List, Sequence, Dict, Any
import json
import logging

from app.core.database import database_manager
from app.dao.base import BaseDAO
from app.models.users import User, UserLog
from app.models.roles import Role

logger = logging.getLogger(__name__)

class UserDAO(BaseDAO):
    model = User

    def __init__(self, session=None):
        self.session = session

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Найти пользователя по ID"""
        return await self.find_one_or_none(id=user_id)

    async def get_user_by_email(self, user_email: str) -> Optional[User]:
        """Найти пользователя по email"""
        return await self.find_one_or_none(user_email=user_email)

    async def get_user_by_phone(self, user_phone: str) -> Optional[User]:
        """Найти пользователя по телефону"""
        return await self.find_one_or_none(user_phone=user_phone)

    async def get_user_with_role(self, user_id: int) -> Optional[User]:
        """Найти пользователя с информацией о роли"""
        async with database_manager.get_session() as session:
            query = select(self.model).options(joinedload(self.model.role)).filter_by(id=user_id)
            result = await session.execute(query)
            return result.unique().scalar_one_or_none()

    async def get_all_users_with_roles(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получить всех пользователей с ролями"""
        async with database_manager.get_session() as session:
            query = (select(self.model)
                    .options(joinedload(self.model.role))
                    .offset(skip)
                    .limit(limit))
            result = await session.execute(query)
            users: Sequence[User] = result.unique().scalars().all()
            return list(users)  # Преобразуем Sequence в List

    async def update_user_role(self, user_id: int, new_role_id: int) -> bool:
        """Обновить роль пользователя с обновлением счетчиков"""
        async with database_manager.get_session() as session:
            async with session.begin():
                # Находим пользователя
                user = await self.get_user_by_id(user_id)
                if not user:
                    return False
                
                old_role_id = user.role_id
                
                # Если роль не изменилась
                if old_role_id == new_role_id:
                    return True
                
                # Обновляем роль
                stmt = update(self.model).where(
                    self.model.id == user_id
                ).values(role_id=new_role_id)
                await session.execute(stmt)
                
                # Обновляем счетчики ролей
                if old_role_id:
                    await Role.decrement_count(old_role_id)
                await Role.increment_count(new_role_id)
                
                await session.commit()
                return True

    async def update_last_login(self, user_id: int) -> bool:
        """Обновить время последнего входа"""
        from datetime import datetime
        current_time = datetime.now()
        
        return await self.update(
            filter_by={'id': user_id},
            last_login=current_time
        ) > 0

    async def update_user_profile(self, user_id: int, **update_data) -> bool:
        """Обновить профиль пользователя"""
        excluded_fields = {'id', 'user_pass', 'created_at', 'updated_at'}
        filtered_data = {
            k: v for k, v in update_data.items() 
            if k not in excluded_fields and v is not None
        }
        
        if not filtered_data:
            return False
            
        return await self.update(
            filter_by={'id': user_id},
            **filtered_data
        ) > 0

    async def change_password(self, user_id: int, new_hashed_password: str) -> bool:
        """Изменить пароль пользователя"""
        return await self.update(
            filter_by={'id': user_id},
            user_pass=new_hashed_password
        ) > 0

    async def is_nickname_available(self, user_nick: str, exclude_user_id: Optional[int] = None) -> bool:
        """Проверить доступность никнейма"""
        existing_user = await self.find_one_or_none(user_nick=user_nick)
        if not existing_user:
            return True
            
        if exclude_user_id is not None and existing_user.id == exclude_user_id:
            return True
            
        return False

    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить полный профиль пользователя в виде словаря"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Преобразуем объект User в словарь
        user_dict = {
            "id": user.id,
            "user_phone": user.user_phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_nick": user.user_nick,
            "user_email": user.user_email,
            "two_fa_auth": user.two_fa_auth,
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified,
            "user_status": user.user_status,
            "role_id": user.role_id,
            "tg_chat_id": user.tg_chat_id,
            "last_login": user.last_login,
            "secondary_email": user.secondary_email,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        
        # Парсим security_settings из JSON
        security_settings = {}
        if user.security_settings:
            try:
                security_settings = json.loads(user.security_settings)
            except (json.JSONDecodeError, TypeError):
                security_settings = {}
        
        user_dict["security_settings"] = security_settings
        return user_dict

    async def update_security_settings(self, user_id: int, security_settings: Dict[str, Any]) -> bool:
        """Обновить настройки безопасности пользователя"""
        try:
            settings_json = json.dumps(security_settings, ensure_ascii=False) if security_settings else None
            return await self.update(
                filter_by={'id': user_id},
                security_settings=settings_json
            ) > 0
        except (TypeError, ValueError):
            return False

    async def update_allowed_ips(self, user_id: int, allowed_ips: List[str]) -> bool:
        """Обновить список разрешенных IP"""
        try:
            ips_json = json.dumps(allowed_ips, ensure_ascii=False) if allowed_ips else None
            return await self.update(
                filter_by={'id': user_id},
                allowed_ips=ips_json
            ) > 0
        except (TypeError, ValueError):
            return False

    async def find_by_secondary_email(self, secondary_email: str) -> Optional[User]:
        """Найти пользователя по дополнительному email"""
        return await self.find_one_or_none(secondary_email=secondary_email)

    async def find_user_by_any_email(self, email: str) -> Optional[User]:
        """Найти пользователя по любому email (основному или дополнительному)"""
        if not email:
            return None
            
        async with database_manager.get_session() as session:
            query = select(self.model).filter(
                or_(
                    self.model.user_email == email,
                    self.model.secondary_email == email
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()


class UserLogsDAO(BaseDAO):
    model = UserLog

    async def create_user_log(self, **log_data) -> UserLog:
        """Создать запись в логе пользователя"""
        return await self.add(**log_data)

    async def get_user_logs(self, user_id: int, limit: int = 50, offset: int = 0) -> List[UserLog]:
        """Получить логи пользователя"""
        async with database_manager.get_session() as session:
            query = (select(self.model)
                    .options(
                        joinedload(self.model.user),
                        joinedload(self.model.changer)
                    )
                    .filter_by(user_id=user_id)
                    .order_by(desc(self.model.created_at))
                    .limit(limit)
                    .offset(offset))
            result = await session.execute(query)
            logs: Sequence[UserLog] = result.scalars().all()
            return list(logs)  # Преобразуем Sequence в List

    async def get_recent_role_changes(self, days: int = 30) -> List[UserLog]:
        """Получить recent изменения ролей"""
        from datetime import datetime, timezone, timedelta
        
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        async with database_manager.get_session() as session:
            query = (select(self.model)
                    .options(
                        joinedload(self.model.user),
                        joinedload(self.model.changer)
                    )
                    .filter(
                        self.model.action_type == 'role_change',
                        self.model.created_at >= since_date
                    )
                    .order_by(desc(self.model.created_at)))
            result = await session.execute(query)
            logs: Sequence[UserLog] = result.scalars().all()
            return list(logs)  # Преобразуем Sequence в List