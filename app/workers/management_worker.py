# app/workers/management_worker.py
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from pydantic import BaseModel
from app.core.config import get_settings
from app.services.notification_service import centrifugo_service
from app.dao.redis import redis_dao
from loguru import logger

settings = get_settings()

broker = RabbitBroker(settings.RABBITMQ_URL)
app = FastStream(broker)

class ContainerManagementRequest(BaseModel):
    container_id: str
    user_id: str
    action: str  # stop, restart, pause, etc.

@broker.subscriber("container.management")
async def handle_container_management(request: ContainerManagementRequest):
    """Обработчик управления контейнерами"""
    try:
        logger.info(f"Processing {request.action} for container {request.container_id}")
        
        # Имитация операции управления
        await asyncio.sleep(1)
        
        # Уведомление пользователя
        await centrifugo_service.broadcast_to_user(
            request.user_id,
            f"container_{request.action}",
            {
                "container_id": request.container_id,
                "action": request.action,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Сохраняем статус в Redis
        await redis_dao.set(
            f"container:{request.container_id}:status",
            {
                "action": request.action,
                "status": "completed",
                "user_id": request.user_id,
                "timestamp": datetime.now().isoformat()
            },
            expire=3600
        )
        
        logger.info(f"Container {request.container_id} {request.action} completed")
        
    except Exception as e:
        logger.error(f"Container management failed: {e}")
        await centrifugo_service.broadcast_to_user(
            request.user_id,
            f"container_{request.action}_failed",
            {
                "container_id": request.container_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

if __name__ == "__main__":
    app.run()