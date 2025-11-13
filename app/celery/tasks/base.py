from app.celery.worker import celery_app
from loguru import logger

class BaseTask:
    """Базовый класс для всех задач Celery"""
    
    @classmethod
    def on_success(cls, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} completed successfully")
    
    @classmethod
    def on_failure(cls, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")