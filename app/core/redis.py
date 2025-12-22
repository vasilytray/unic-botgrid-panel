# app/core/redis.py
from redis.asyncio import Redis, ConnectionPool
from app.core.config import get_settings
from loguru import logger

class RedisManager:
    """
    Менеджер Redis подключения - инфраструктурный компонент
    Аналогично DatabaseManager для PostgreSQL
    """
    def __init__(self):
        self.settings = get_settings()
        self.redis: Redis | None = None
        self.pool: ConnectionPool | None = None
    
    async def health_check(self) -> bool:
        """Проверка здоровья подключения"""
        try:
            if self.redis:
                await self.redis.ping() # type: ignore
                return True
            return False
        except Exception:
            return False
        
    async def init_redis(self):
        """Инициализация Redis подключения (как часть инфраструктуры)"""
        try:
            self.pool = ConnectionPool.from_url(
                self.settings.REDIS_URL,
                decode_responses=True,
                max_connections=20
            )
            self.redis = Redis(connection_pool=self.pool)
            
            await self.redis.ping() # type: ignore
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Закрытие подключения (инфраструктурная операция)"""
        if self.redis:
            await self.redis.close()
        if self.pool:
            await self.pool.disconnect()
        logger.info("✅ Redis connection closed")
    
    async def get_redis(self) -> Redis:
        """Получить Redis клиент (инфраструктурный метод)"""
        if not self.redis:
            await self.init_redis()
        return self.redis # type: ignore

# Глобальный экземпляр инфраструктурного компонента
redis_manager = RedisManager()