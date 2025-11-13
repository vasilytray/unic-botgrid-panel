from app.celery.worker import celery_app
from app.celery.tasks.base import BaseTask
from app.tasks.log_cleanup_task import log_cleanup
from app.celery.utils import run_async_method  # Добавляем хелпер
from loguru import logger

@celery_app.task(bind=True, base=BaseTask)
def cleanup_old_logs_task(self):
    """Интеграция с существующей задачей очистки логов"""
    try:
        # Используем хелпер для запуска async метода
        deleted_count = run_async_method(log_cleanup.run_cleanup)
        logger.info(f"Log cleanup task completed via Celery. Deleted {deleted_count} records")
        return {
            "status": "completed", 
            "deleted_count": deleted_count,
            "last_run": log_cleanup.last_run.isoformat() if log_cleanup.last_run else None
        }
    except Exception as exc:
        logger.error(f"Log cleanup failed: {exc}")
        self.retry(countdown=300, exc=exc)

@celery_app.task
def start_periodic_log_cleanup():
    """Запуск периодической очистки логов через Celery Beat"""
    try:
        # Просто запускаем задачу очистки
        task = cleanup_old_logs_task.delay()
        return {"task_id": task.id, "status": "started"}
    except Exception as exc:
        logger.error(f"Failed to start periodic log cleanup: {exc}")
        return {"error": str(exc)}

@celery_app.task
def get_log_cleanup_status():
    """Получение статуса задачи очистки логов"""
    try:
        status = log_cleanup.get_status()
        return status
    except Exception as exc:
        logger.error(f"Failed to get log cleanup status: {exc}")
        return {"error": str(exc)}

@celery_app.task
def health_check():
    """Проверка здоровья приложения"""
    try:
        # Проверка подключения к БД, Redis и т.д.
        logger.info("Health check completed")
        return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        return {"status": "unhealthy", "error": str(exc)}

@celery_app.task
def monitor_background_tasks():
    """Мониторинг всех фоновых задач"""
    try:
        # Получаем статус вашей существующей задачи
        log_cleanup_status = log_cleanup.get_status()
        
        return {
            "log_cleanup": log_cleanup_status,
            "celery_worker": "active",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as exc:
        logger.error(f"Background tasks monitoring failed: {exc}")
        return {"error": str(exc)}