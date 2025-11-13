# app/celery/worker.py

from celery import Celery
from app.celery.config import CeleryConfig

def create_celery_app():
    celery_app = Celery("app.celery")
    
    # Конфигурация
    celery_app.config_from_object(CeleryConfig)
    
    # Автоматическое обнаружение задач
    celery_app.autodiscover_tasks([
        'app.celery.tasks.user_tasks',
        'app.celery.tasks.ticket_tasks',
        'app.celery.tasks.monitoring_tasks',
        'app.celery.tasks.email_tasks',
        'app.celery.tasks.ai_tasks',
        'app.celery.tasks.billing_tasks',
        'app.celery.tasks.deployment_tasks'
        
    ])
    
    return celery_app

celery_app = create_celery_app()