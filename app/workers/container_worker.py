# app/workers/container_worker.py
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from pydantic import BaseModel
from app.core.config import get_settings
from app.services.notification_service import centrifugo_service
from app.dao.redis import redis_dao
import asyncio
import uuid
from datetime import datetime
from loguru import logger

settings = get_settings()

broker = RabbitBroker(settings.RABBITMQ_URL)
app = FastStream(broker)

class ContainerDeployRequest(BaseModel):
    user_id: str
    image: str
    config: dict
    resources: dict

class ContainerMetrics(BaseModel):
    container_id: str
    cpu_usage: float
    memory_usage: int
    network_io: dict

@broker.subscriber("container.deploy")
async def handle_container_deploy(request: ContainerDeployRequest):
    """Обработчик деплоя контейнеров"""
    try:
        container_id = f"container_{uuid.uuid4().hex[:8]}"
        
        # Имитация деплоя
        await asyncio.sleep(2)
        
        # Уведомление через Centrifugo
        await centrifugo_service.broadcast_to_user(
            request.user_id,
            "container_deployed",
            {
                "container_id": container_id,
                "status": "running",
                "image": request.image,
                "deployed_at": datetime.now().isoformat()
            }
        )
        
        # Сохраняем в Redis
        await redis_dao.set(
            f"deployment:{container_id}",
            {
                "user_id": request.user_id,
                "image": request.image,
                "status": "deployed",
                "deployed_at": datetime.now().isoformat()
            },
            expire=3600
        )
        
        logger.info(f"Container {container_id} deployed for user {request.user_id}")
        
    except Exception as e:
        logger.error(f"Container deployment failed: {e}")
        await centrifugo_service.broadcast_to_user(
            request.user_id,
            "container_deploy_failed",
            {"error": str(e), "timestamp": datetime.now().isoformat()}
        )

@broker.subscriber("metrics.collect")
async def process_metrics(metrics: ContainerMetrics):
    """Обработка метрик контейнеров в реальном времени"""
    try:
        metrics_data = metrics.model_dump()
        metrics_data["timestamp"] = datetime.now().isoformat()
        
        await redis_dao.set(
            f"metrics:{metrics.container_id}",
            metrics_data,
            expire=60
        )
        
        await centrifugo_service.publish(
            f"containers:{metrics.container_id}",
            {
                "type": "metrics_update", 
                "data": metrics_data,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.debug(f"Metrics updated for container {metrics.container_id}")
        
    except Exception as e:
        logger.error(f"Metrics processing failed: {e}")

@app.after_startup
async def on_startup():
    """Инициализация при запуске worker"""
    logger.info("✅ Container worker started")

@app.after_shutdown
async def on_shutdown():
    """Очистка при остановке worker"""
    logger.info("✅ Container worker stopped")

async def main():
    """Основная асинхронная функция"""
    await app.run()

if __name__ == "__main__":
    # ИСПРАВЛЕНО: запускаем асинхронно
    asyncio.run(main())