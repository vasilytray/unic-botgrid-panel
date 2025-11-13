from app.celery.worker import celery_app
from app.celery.tasks.base import BaseTask
from app.users.dao import UsersDAO
from app.verificationcodes.dao import VerificationCodeDAO
from loguru import logger

@celery_app.task(bind=True, base=BaseTask, max_retries=3)
def send_verification_email(self, user_id: int, email: str, code: str):
    """Отправка email с кодом верификации"""
    try:
        # TODO: Интеграция с email сервисом
        logger.info(f"Sending verification code {code} to user {user_id} at {email}")
        # Имитация отправки
        logger.success(f"Verification email sent to {email}")
        return {"status": "sent", "user_id": user_id, "email": email}
    except Exception as exc:
        logger.error(f"Failed to send verification email: {exc}")
        self.retry(countdown=60, exc=exc)

@celery_app.task
def cleanup_expired_verification_codes():
    """Очистка просроченных кодов верификации"""
    try:
        deleted_count = VerificationCodeDAO.cleanup_expired()
        logger.info(f"Cleaned up {deleted_count} expired verification codes")
        return {"deleted_count": deleted_count}
    except Exception as exc:
        logger.error(f"Failed to cleanup verification codes: {exc}")
        return {"error": str(exc)}

@celery_app.task(bind=True, base=BaseTask)
def process_user_registration(self, user_data: dict):
    """Обработка регистрации пользователя (для тяжелых операций)"""
    try:
        logger.info(f"Processing registration for user: {user_data.get('email')}")
        # Тяжелые операции: валидация, создание профиля, инициализация и т.д.
        return {"status": "processed", "user_email": user_data.get('email')}
    except Exception as exc:
        logger.error(f"User registration processing failed: {exc}")
        self.retry(countdown=30, exc=exc)