# app/dao/redis.py
from typing import Optional, Any, List, Dict
import json
from app.core.config import get_settings
from app.core.redis import redis_manager
from loguru import logger

class RedisDAO:
    """
    Data Access Object для Redis операций
    Реализует конкретные методы доступа к данным
    """
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить данные по ключу"""
        try:
            redis = await redis_manager.get_redis()
            data = await redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Сохранить данные с TTL"""
        try:
            redis = await redis_manager.get_redis()
            await redis.setex(
                key, expire, 
                json.dumps(value, default=str, ensure_ascii=False)
            )
            return True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удалить ключ"""
        try:
            redis = await redis_manager.get_redis()
            result = await redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False
    
    async def hset(self, key: str, field: str, value: Any) -> bool:
        """Установить значение поля хеша"""
        try:
            redis = await redis_manager.get_redis()
            value_str = json.dumps(value, default=str) if not isinstance(value, (str, int, float)) else str(value)
            result = await redis.hset(key, field, value_str) # type: ignore
            return result > 0
        except Exception as e:
            logger.error(f"Error setting hash field {field}: {e}")
            return False
    
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Получить значение поля хеша"""
        try:
            redis = await redis_manager.get_redis()
            value = await redis.hget(key, field) # type: ignore
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Error getting hash field {field}: {e}")
            return None

    # Методы для обратной совместимости
    async def cache_set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Алиас для set (обратная совместимость)"""
        return await self.set(key, value, expire)
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Алиас для get (обратная совместимость)"""
        return await self.get(key)
    
    async def init_redis(self):
        """Пустой метод для обратной совместимости"""
        # Redis уже инициализирован через redis_manager в lifespan
        pass
    
    async def close(self):
        """Пустой метод для обратной совместимости"""
        # Закрытие управляется через redis_manager в lifespan
        pass

# Глобальный экземпляр DAO
redis_dao = RedisDAO()