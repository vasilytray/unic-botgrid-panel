# app/core/rabbitmq.py
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from app.core.config import get_settings
from loguru import logger

settings = get_settings()

class RabbitMQManager:
    def __init__(self):
        self.broker: RabbitBroker | None = None
        self.app: FastStream | None = None
    
    async def init_broker(self):
        """Инициализация RabbitMQ брокера"""
        try:
            self.broker = RabbitBroker(settings.RABBITMQ_URL)
            self.app = FastStream(self.broker)
            
            # Тестовое подключение
            await self.broker.connect()
            await self.broker.close()
            
            logger.info("✅ RabbitMQ connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            raise
    
    def get_broker(self) -> RabbitBroker:
        """Получить брокер"""
        if not self.broker:
            raise RuntimeError("RabbitMQ broker not initialized")
        return self.broker

# Глобальный экземпляр
rabbitmq_manager = RabbitMQManager()