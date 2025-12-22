# app/utils/broker_utils.py
from faststream.rabbit import RabbitBroker
from app.core.config import get_settings
from loguru import logger

settings = get_settings()

class BrokerManager:
    """Менеджер для работы с RabbitMQ брокером"""
    
    @staticmethod
    async def publish_message(message: dict, queue: str):
        """Публикация сообщения в очередь"""
        broker = None
        try:
            broker = RabbitBroker(settings.RABBITMQ_URL)
            await broker.start()
            await broker.publish(message, queue)
            logger.info(f"Message published to {queue}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message to {queue}: {e}")
            return False
        finally:
            if broker:
                await broker.stop()
    
    @staticmethod
    async def publish_with_exchange(message: dict, exchange: str, routing_key: str = ""):
        """Публикация сообщения в exchange"""
        broker = None
        try:
            broker = RabbitBroker(settings.RABBITMQ_URL)
            await broker.start()
            await broker.publish(message, exchange, routing_key=routing_key)
            logger.info(f"Message published to exchange {exchange}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to exchange {exchange}: {e}")
            return False
        finally:
            if broker:
                await broker.stop()

# Глобальный экземпляр
broker_manager = BrokerManager()