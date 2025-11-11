# app/celery/config.py
from app.config import settings

class CeleryConfig:
    broker_url = settings.CELERY_BROKER_URL
    result_backend = settings.CELERY_RESULT_BACKEND
    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]
    timezone = "UTC"
    enable_utc = True
    
    # Важные настройки для свежих версий
    broker_connection_retry_on_startup = True
    task_track_started = True
    task_always_eager = False
    
    # Периодические задачи (Beat)
    beat_schedule = {
        'cleanup-old-logs': {
            'task': 'app.celery.tasks.monitoring_tasks.cleanup_old_logs',
            'schedule': 86400.0,  # каждые 24 часа
        },
        'check-services-health': {
            'task': 'app.celery.tasks.monitoring_tasks.check_services_health',
            'schedule': 300.0,  # каждые 5 минут
        },
        'process-pending-payments': {
            'task': 'app.celery.tasks.billing_tasks.process_pending_payments',
            'schedule': 600.0,  # каждые 10 минут
        }
    }