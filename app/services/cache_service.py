# app/services/cache_service.py
from app.dao.redis import redis_dao
from app.dao.users import UserDAO
from loguru import logger

class CacheService:
    """
    Сервис кеширования - бизнес-логика работы с кешем
    """
    
    def __init__(self, user_dao: UserDAO):
        self.user_dao = user_dao
        self.redis_dao = redis_dao
    
    async def cache_user_profile(self, user_id: int) -> bool:
        """Кешировать профиль пользователя"""
        user = await self.user_dao.get(user_id)
        if not user:
            return False
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active
        }
        
        cache_key = f"user_profile:{user_id}"
        return await self.redis_dao.set(cache_key, user_data, expire=3600)
    
    async def get_cached_user_profile(self, user_id: int) -> Optional[dict]:
        """Получить кешированный профиль пользователя"""
        cache_key = f"user_profile:{user_id}"
        return await self.redis_dao.get(cache_key)
    
    async def invalidate_user_cache(self, user_id: int) -> bool:
        """Инвалидировать кеш пользователя"""
        cache_key = f"user_profile:{user_id}"
        return await self.redis_dao.delete(cache_key)

# Пример использования в UserService
class UserService:
    def __init__(self, db):
        self.user_dao = UserDAO(db)
        self.cache_service = CacheService(self.user_dao)
    
    async def get_user_with_cache(self, user_id: int):
        # Сначала проверяем кеш
        cached_user = await self.cache_service.get_cached_user_profile(user_id)
        if cached_user:
            logger.info(f"Cache hit for user {user_id}")
            return cached_user
        
        # Если нет в кеше - получаем из БД и кешируем
        user = await self.user_dao.get(user_id)
        if user:
            await self.cache_service.cache_user_profile(user_id)
        
        return user