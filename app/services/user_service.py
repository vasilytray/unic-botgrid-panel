# app/services/user_service.py
from typing import Optional, Dict, Any
from app.dao.users import UserDAO
from app.dao.redis import RedisDAO
from app.core.security import security_manager
from app.core.exceptions import IncorrectEmailOrPasswordException, UserAlreadyExistsException
from app.models.users import User

class UserService:
    def __init__(self, user_dao: UserDAO, redis_dao: RedisDAO):
        self.user_dao = user_dao
        self.redis_dao = redis_dao
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя с кешированием"""
        # Пробуем получить из кеша
        cache_key = f"user_auth:{email}"
        cached_user_data = await self.redis_dao.cache_get(cache_key)
        
        if cached_user_data:
            # Проверяем пароль (кеш не должен содержать пароль для безопасности)
            # Поэтому всегда идем в БД для проверки пароля
            pass
        
        # Ищем в БД
        user = await self.user_dao.get_user_by_email(email)
        if not user or not security_manager.verify_password(password, user.user_pass):
            raise IncorrectEmailOrPasswordException
        
        # Сохраняем в кеш (без пароля для безопасности)
        user_data = {
            "id": user.id,
            "user_email": user.user_email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_nick": user.user_nick,
            "role_id": user.role_id,
            "two_fa_auth": user.two_fa_auth,
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified
        }
        await self.redis_dao.cache_set(cache_key, user_data, expire=300)
        
        return user
    
    async def create_user(self, user_data: Dict[str, Any]) -> int:
        """Создание пользователя с валидацией"""
        # Проверяем уникальность email
        if await self.user_dao.get_user_by_email(user_data["user_email"]):
            raise UserAlreadyExistsException
        
        # Проверяем уникальность телефона
        if await self.user_dao.get_user_by_phone(user_data["user_phone"]):
            raise UserAlreadyExistsException
        
        # Хешируем пароль
        if "user_pass" in user_data:
            user_data["user_pass"] = security_manager.get_password_hash(user_data["user_pass"])
        
        # Создаем пользователя
        user_id = await self.user_dao.add(**user_data)
        
        # Инвалидируем кеш
        await self.redis_dao.delete(f"user_auth:{user_data['user_email']}")
        
        return user_id
    
    async def get_user_profile_with_cache(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить профиль пользователя с кешированием"""
        cache_key = f"user_profile:{user_id}"
        cached_profile = await self.redis_dao.cache_get(cache_key)
        
        if cached_profile:
            return cached_profile
        
        # Получаем из БД
        profile = await self.user_dao.get_user_profile(user_id)
        if profile:
            await self.redis_dao.cache_set(cache_key, profile, expire=600)
        
        return profile
    
    async def update_user_profile_with_cache(self, user_id: int, **update_data) -> bool:
        """Обновить профиль пользователя с инвалидацией кеша"""
        success = await self.user_dao.update_user_profile(user_id, **update_data)
        
        if success:
            # Инвалидируем кеш профиля
            await self.redis_dao.delete(f"user_profile:{user_id}")
            
            # Если обновляется email, инвалидируем кеш аутентификации
            if "user_email" in update_data:
                user = await self.user_dao.get_user_by_id(user_id)
                if user:
                    await self.redis_dao.delete(f"user_auth:{user.user_email}")
        
        return success
    
    async def search_users(self, query: str, limit: int = 10) -> list[User]:
        """Поиск пользователей по имени, email или телефону"""
        # Пробуем получить из кеша
        cache_key = f"user_search:{query}:{limit}"
        cached_results = await self.redis_dao.cache_get(cache_key)
        
        if cached_results:
            return [User(**user_data) for user_data in cached_results]
        
        # Ищем в БД
        users = []
        # Здесь должна быть логика поиска по разным полям
        # Пока просто возвращаем пустой список
        # В реальной реализации нужно добавить поиск по БД
        
        # Сохраняем в кеш
        if users:
            users_data = [user.to_dict() for user in users]
            await self.redis_dao.cache_set(cache_key, users_data, expire=300)
        
        return users