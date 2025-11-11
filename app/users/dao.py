from sqlalchemy import select, delete, desc, update, or_
from sqlalchemy.orm import joinedload
from app.dao.base import BaseDAO
from app.users.models import User, UserLog
from app.roles.models import Role
from app.database import async_session_maker
from datetime import datetime, timezone, timedelta
import logging
import json  # Добавляем импорт json
import re

# Система логирования
DEBUG_LEVEL = 0 # 0 - нет логов, 1 - ошибки, 2 - предупреждения, 3 - все логи
logger = logging.getLogger(__name__)

if (DEBUG_LEVEL >= 1):
    def log_info(message: str):
        logger.info(message)
    
    def log_error(message: str):
        logger.error(message)
    
    def log_success(message: str):
        logger.info(f"✅ {message}")


class UsersDAO(BaseDAO):
    model = User

    @classmethod
    async def find_full_data(cls, user_id: int):
        """Найти пользователя с полными данными (включая роль)"""
        return await cls.find_one_or_none(id=user_id)

    @classmethod
    async def find_all_with_roles(cls, **filter_by):
        """Найти всех пользователей с загруженными ролями"""
        async with async_session_maker() as session:
            query = select(cls.model).options(joinedload(cls.model.role)).filter_by(**filter_by)
            result = await session.execute(query)
            return result.unique().scalars().all()

    @classmethod
    async def find_by_email(cls, user_email: str):
        """Найти пользователя по email"""
        return await cls.find_one_or_none(user_email=user_email)
    
    @classmethod
    async def find_by_email_with_role(cls, user_email: str):
        """Найти пользователя по email с загруженной ролью"""
        async with async_session_maker() as session:
            query = select(cls.model).options(joinedload(cls.model.role)).filter_by(user_email=user_email)
            result = await session.execute(query)
            return result.unique().scalar_one_or_none()

    @classmethod
    async def find_by_phone(cls, user_phone: str):
        """Найти пользователя по телефону"""
        return await cls.find_one_or_none(user_phone=user_phone)

    @classmethod
    async def update_user_role(cls, user_id: int, new_role_id: int) -> bool:
        """Обновить роль пользователя с обновлением счетчиков"""
        async with async_session_maker() as session:
            async with session.begin():
                # Находим пользователя и его текущую роль
                user = await cls.find_one_or_none_by_id(user_id)
                if not user:
                    return False
                
                old_role_id = user.role_id
                
                # Если роль не изменилась, ничего не делаем
                if old_role_id == new_role_id:
                    return True
                
                # Обновляем роль пользователя
                result = await cls.update(
                    filter_by={'id': user_id},
                    role_id=new_role_id
                )
                
                if result > 0:
                    # Обновляем счетчики ролей
                    if old_role_id:
                        await Role.decrement_count(old_role_id)
                    await Role.increment_count(new_role_id)
                
                return result > 0

    @classmethod
    async def update_user_role_by_email(cls, user_email: str, new_role_id: int) -> bool:
        """Обновить роль пользователя по email с обновлением счетчиков"""
        async with async_session_maker() as session:
            async with session.begin():
                # Находим пользователя и его текущую роль
                user = await cls.find_by_email(user_email)
                if not user:
                    return False
                
                old_role_id = user.role_id
                
                # Если роль не изменилась, ничего не делаем
                if old_role_id == new_role_id:
                    return True
                
                # Обновляем роль пользователя
                result = await cls.update(
                    filter_by={'user_email': user_email},
                    role_id=new_role_id
                )
                
                if result > 0:
                    # Обновляем счетчики ролей
                    if old_role_id:
                        await Role.decrement_count(old_role_id)
                    await Role.increment_count(new_role_id)
                
                return result > 0

    @classmethod
    async def add_user(cls, **user_data: dict):
        """Добавить пользователя с обновлением счетчика роли"""
        async with async_session_maker() as session:
            async with session.begin():
                new_user = cls.model(**user_data)
                session.add(new_user)
                await session.flush()
                new_user_id = new_user.id
                
                # Обновляем счетчик роли
                role_id = user_data.get('role_id')
                if role_id:
                    await Role.increment_count(role_id)
                
                await session.commit()
                return new_user_id

    @classmethod
    async def delete_user_by_id(cls, user_id: int):
        """Удалить пользователя с обновлением счетчика роли"""
        async with async_session_maker() as session:
            async with session.begin():
                # Находим пользователя
                user = await cls.find_one_or_none_by_id(user_id)
                if not user:
                    return False
                
                role_id = user.role_id
                
                # Удаляем пользователя
                result = await cls.delete(id=user_id)
                
                if result > 0 and role_id:
                    # Обновляем счетчик роли
                    await Role.decrement_count(role_id)
                
                return result > 0

    @classmethod
    async def get_user_with_role_info(cls, user_id: int):
        """Получить пользователя с информацией о роли"""
        async with async_session_maker() as session:
            query = select(cls.model).options(joinedload(cls.model.role)).filter_by(id=user_id)
            result = await session.execute(query)
            return result.unique().scalar_one_or_none()

    @classmethod
    async def get_user_with_role_info_by_email(cls, user_email: str):
        """Получить пользователя с информацией о роли по email"""
        async with async_session_maker() as session:
            query = select(cls.model).options(joinedload(cls.model.role)).filter_by(user_email=user_email)
            result = await session.execute(query)
            return result.unique().scalar_one_or_none()
        
    @classmethod
    async def update_last_login(cls, user_id: int):
        """Обновить время последнего входа пользователя"""
        async with async_session_maker() as session:
            try:
                # Используем datetime без временной зоны
                from datetime import datetime
                current_time = datetime.now()  # Без timezone!

                print(f"🔄 Обновление last_login для пользователя {user_id}: {current_time}")

                # Прямое обновление без загрузки объекта
                stmt = (
                    update(cls.model)
                    .where(cls.model.id == user_id)
                    .values(last_login=current_time)
                )
                result = await session.execute(stmt)
                await session.commit()

                print(f"✅ Last_login обновлен для пользователя {user_id}")
                return result.rowcount > 0

            except Exception as e:
                print(f"❌ Ошибка при обновлении last_login: {e}")
                await session.rollback()
                return False

    # НОВЫЕ МЕТОДЫ ДЛЯ ОБНОВЛЕНИЯ ПРОФИЛЯ
    
    @classmethod
    async def update_user_profile(cls, user_id: int, **update_data) -> bool:
        """Обновляет профиль пользователя"""
        # Убираем поля, которые не нужно обновлять
        excluded_fields = {'id', 'user_pass', 'created_at', 'updated_at'}
        filtered_data = {k: v for k, v in update_data.items() if k not in excluded_fields and v is not None}
        
        if not filtered_data:
            return False
            
        return await cls.update(
            filter_by={'id': user_id},
            **filtered_data
        ) > 0
    
    @classmethod
    async def change_password(cls, user_id: int, new_hashed_password: str) -> bool:
        """Изменяет пароль пользователя"""
        return await cls.update(
            filter_by={'id': user_id},
            user_pass=new_hashed_password
        ) > 0
    
    @classmethod
    async def verify_current_password(cls, user_id: int, plain_password: str) -> bool:
        """Проверяет текущий пароль"""
        user = await cls.find_one_or_none_by_id(user_id)
        if not user:
            return False
        
        from app.users.auth import verify_password
        return verify_password(plain_password, user.user_pass)
    
    @classmethod
    async def update_security_settings(cls, user_id: int, settings: dict) -> bool:
        """Обновляет настройки безопасности"""
        settings_json = json.dumps(settings, ensure_ascii=False) if settings else None
        return await cls.update(
            filter_by={'id': user_id},
            security_settings=settings_json
        ) > 0
    
    @classmethod
    async def update_allowed_ips(cls, user_id: int, allowed_ips: list) -> bool:
        """Обновляет список разрешенных IP"""
        ips_json = json.dumps(allowed_ips, ensure_ascii=False) if allowed_ips else None
        return await cls.update(
            filter_by={'id': user_id},
            allowed_ips=ips_json
        ) > 0
    
    @classmethod
    async def get_user_profile(cls, user_id: int):
        """Получает полный профиль пользователя"""
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            
            if user:
                # Парсим настройки безопасности
                security_settings = {}
                if user.security_settings:
                    try:
                        security_settings = json.loads(user.security_settings)
                    except (json.JSONDecodeError, TypeError):
                        security_settings = {}
                
                # Добавляем распарсенные настройки как атрибут
                user.security_settings = security_settings
            
            return user
    
    @classmethod
    async def is_nickname_available(cls, user_nick: str, exclude_user_id: int = None) -> bool:
        """Проверяет доступность никнейма"""
        if not user_nick:
            return False
            
        existing_user = await cls.find_one_or_none(user_nick=user_nick)
        if not existing_user:
            return True
            
        # Если передан exclude_user_id, проверяем что это тот же пользователь
        if exclude_user_id and existing_user.id == exclude_user_id:
            return True
            
        return False
    
    @classmethod
    async def find_by_nickname(cls, user_nick: str):
        """Найти пользователя по никнейму"""
        return await cls.find_one_or_none(user_nick=user_nick)
    
    @classmethod
    async def find_by_secondary_email(cls, secondary_email: str):
        """Найти пользователя по дополнительному email"""
        if not secondary_email:
            return None
            
        async with async_session_maker() as session:
            query = select(cls.model).filter(
                cls.model.secondary_email == secondary_email,
                cls.model.secondary_email.isnot(None)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_user_by_any_email(cls, email: str):
        """Найти пользователя по любому email (основному или дополнительному)"""
        if not email:
            return None
            
        async with async_session_maker() as session:
            query = select(cls.model).filter(
                or_(
                    cls.model.user_email == email,
                    cls.model.secondary_email == email
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        
class UserLogsDAO(BaseDAO):
    model = UserLog

    @classmethod
    async def create_log(cls, **log_data: dict):
        """Создать запись в логе"""
        return await cls.add(**log_data)

    @classmethod
    async def get_user_logs(cls, user_id: int, limit: int = 50, offset: int = 0):
        """Получить логи пользователя"""
        async with async_session_maker() as session:
            query = (select(cls.model)
                    .options(
                        joinedload(cls.model.user),
                        joinedload(cls.model.changer)
                    )
                    .filter_by(user_id=user_id)
                    .order_by(desc(cls.model.created_at))
                    .limit(limit)
                    .offset(offset))
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_role_change_logs(cls, user_id: int = None, limit: int = 50):
        """Получить логи изменения ролей"""
        async with async_session_maker() as session:
            query = (select(cls.model)
                    .options(
                        joinedload(cls.model.user),
                        joinedload(cls.model.changer)
                    )
                    .filter_by(action_type='role_change'))
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            query = query.order_by(desc(cls.model.created_at)).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_recent_role_changes(cls, days: int = 30):
        """Получить recent изменения ролей за указанное количество дней"""
        async with async_session_maker() as session:
            # Используем timezone-aware datetime
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = (select(cls.model)
                    .options(
                        joinedload(cls.model.user),
                        joinedload(cls.model.changer)
                    )
                    .filter(
                        cls.model.action_type == 'role_change',
                        cls.model.created_at >= since_date
                    )
                    .order_by(desc(cls.model.created_at)))
            result = await session.execute(query)
            return result.scalars().all()