from app.celery.worker import celery_app
from app.celery.tasks.base import BaseTask
from loguru import logger

@celery_app.task(bind=True, base=BaseTask, max_retries=3)
def send_email(self, to_email: str, subject: str, template_name: str, context: dict):
    """Универсальная задача отправки email"""
    try:
        # TODO: Интеграция с SMTP/Email API
        logger.info(f"Sending email '{subject}' to {to_email}")
        
        # Имитация отправки
        logger.success(f"Email sent to {to_email}")
        
        return {
            "status": "sent",
            "to": to_email,
            "subject": subject,
            "template": template_name
        }
    except Exception as exc:
        logger.error(f"Email sending failed: {exc}")
        self.retry(countdown=60, exc=exc)