# app/services/notification_service.py
from datetime import datetime
import httpx
from app.core.config import get_settings
from app.dao.redis import RedisDAO

from loguru import logger

class NotificationService:
    def __init__(self, redis_dao: RedisDAO):
        self.redis_dao = redis_dao
        self.settings=get_settings()
        self.centrifugo_url = self.settings.CENTRIFUGO_URL
        self.api_key = self.settings.CENTRIFUGO_API_KEY
    
    async def publish_to_user(self, user_id: str, event_type: str, data: dict):
        """Публикация уведомления пользователю"""
        # Кешируем уведомление
        await self.redis_dao.set(
            f"notification:{user_id}:{event_type}",
            data,
            expire=3600
        )
        
        # Отправляем через Centrifugo
        if self.api_key:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.centrifugo_url}/api/publish",
                    json={
                        "channel": f"user:{user_id}",
                        "data": {
                            "type": event_type,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    },
                    headers={"X-API-Key": self.api_key}
                )

class CentrifugoService:
    def __init__(self):
        self.settings=get_settings()
        self.api_url = self.settings.CENTRIFUGO_URL
        self.api_key = self.settings.CENTRIFUGO_API_KEY
        self.secret_key = self.settings.CENTRIFUGO_SECRET_KEY
    
    async def publish(self, channel: str, data: dict):
        """Публикация сообщения в канал"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/api/publish",
                    json={
                        "channel": channel,
                        "data": data
                    },
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    } # type: ignore
                )
                return response.json()
        except Exception as e:
            logger.error(f"Centrifugo publish error: {e}")
            return None
    
    async def broadcast_to_user(self, user_id: str, event_type: str, data: dict):
        """Отправка уведомления конкретному пользователю"""
        return await self.publish(
            f"user:{user_id}",
            {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def broadcast_to_admins(self, event_type: str, data: dict):
        """Отправка уведомления всем админам"""
        return await self.publish(
            "admin:notifications",
            {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        )

# Глобальный экземпляр
notification_service = NotificationService()
centrifugo_service = CentrifugoService()