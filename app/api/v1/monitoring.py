# app/api/v1/monitoring.py
# API для мониторинга workers
from fastapi import APIRouter, Depends
from app.dao.redis import RedisDAO

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/workers")
async def get_workers_status(redis_dao: RedisDAO = Depends(get_redis_dao)):
    """Получить статус всех workers"""
    workers_info = await redis_dao.hgetall("workers:status")
    return {"workers": workers_info}

@router.get("/queue-stats")
async def get_queue_stats(redis_dao: RedisDAO = Depends(get_redis_dao)):
    """Статистика очередей"""
    stats = await redis_dao.hgetall("rabbitmq:stats")
    return {"queue_stats": stats}