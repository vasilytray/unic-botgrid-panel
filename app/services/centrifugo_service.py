# app/services/centrifugo_service.py
import httpx
# import jwt
import time
from jose import jwt
from app.core.config import get_settings, get_auth_cent_data
from loguru import logger


class CentrifugoService:
    def __init__(self):
        self.settings = get_settings()
        self.api_url = f"{self.settings.CENTRIFUGO_URL}/api"
        self.api_key = self.settings.CENTRIFUGO_API_KEY
        self.secret_key = self.settings.CENTRIFUGO_SECRET_KEY
    
    def generate_user_token(self, user_id: str, exp: int = 3600) -> str:
        """Генерация JWT токена для Centrifugo"""
        payload = {
            "sub": str(user_id),
            "exp": int(time.time()) + exp
        }
        auth_data = get_auth_cent_data()
        return jwt.encode(payload, auth_data['secret_key'], algorithm="HS256")
    
    async def publish(self, channel: str, data: dict) -> bool:
        """Публикация сообщения в канал"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_url}/publish",
                    json={
                        "channel": channel,
                        "data": data
                    },
                    headers={
                        "Authorization": f"apikey {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    logger.debug(f"✅ Message published to {channel}")
                    return True
                else:
                    logger.error(f"❌ Centrifugo publish failed: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Centrifugo error: {e}")
            return False
    
    async def broadcast_to_user(self, user_id: str, event: str, data: dict) -> bool:
        """Отправка сообщения конкретному пользователю"""
        channel = f"user:{user_id}"
        message = {
            "event": event,
            "data": data,
            "timestamp": time.time()
        }
        return await self.publish(channel, message)
    
    async def broadcast_to_admins(self, event: str, data: dict) -> bool:
        """Отправка сообщения всем администраторам"""
        channel = "admin:notifications"
        message = {
            "event": event,
            "data": data,
            "timestamp": time.time()
        }
        return await self.publish(channel, message)
    
    async def broadcast_to_channel(self, channel: str, event: str, data: dict) -> bool:
        """Отправка сообщения в произвольный канал"""
        message = {
            "event": event,
            "data": data,
            "timestamp": time.time()
        }
        return await self.publish(channel, message)

# Глобальный экземпляр
centrifugo_service = CentrifugoService()