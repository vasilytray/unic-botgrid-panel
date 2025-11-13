from app.celery.worker import celery_app
from app.celery.tasks.base import BaseTask
from app.tickets.dao import TicketDAO
from app.celery.utils import run_async_method  # Добавляем хелпер
from loguru import logger

@celery_app.task(bind=True, base=BaseTask, max_retries=3)
def send_ticket_notification(self, ticket_id: int, notification_type: str):
    """Отправка уведомлений о тикетах"""
    try:
        # Используем хелпер для async метода
        ticket = run_async_method(TicketDAO.get_ticket, ticket_id)
        if not ticket:
            logger.warning(f"Ticket {ticket_id} not found")
            return
        
        # TODO: Интеграция с системой уведомлений
        logger.info(f"Sending {notification_type} notification for ticket {ticket_id}")
        
        return {
            "status": "sent", 
            "ticket_id": ticket_id, 
            "type": notification_type
        }
    except Exception as exc:
        logger.error(f"Ticket notification failed: {exc}")
        self.retry(countdown=30, exc=exc)

@celery_app.task
def auto_close_resolved_tickets():
    """Автоматическое закрытие решенных тикетов"""
    try:
        # Используем хелпер для async метода
        closed_count = run_async_method(TicketDAO.auto_close_resolved)
        logger.info(f"Auto-closed {closed_count} resolved tickets")
        return {"closed_count": closed_count}
    except Exception as exc:
        logger.error(f"Auto-close tickets failed: {exc}")
        return {"error": str(exc)}

@celery_app.task(bind=True, base=BaseTask)
def process_ticket_attachments(self, ticket_id: int, attachments: list):
    """Обработка вложений тикета (сжатие, валидация и т.д.)"""
    try:
        logger.info(f"Processing {len(attachments)} attachments for ticket {ticket_id}")
        # Тяжелые операции с файлами
        return {
            "status": "processed", 
            "ticket_id": ticket_id, 
            "attachments_count": len(attachments)
        }
    except Exception as exc:
        logger.error(f"Ticket attachments processing failed: {exc}")
        self.retry(countdown=60, exc=exc)