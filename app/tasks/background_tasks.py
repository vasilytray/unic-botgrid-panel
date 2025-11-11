import asyncio
import logging
from datetime import datetime, timezone
from app.users.log_cleaner import LogCleaner

logger = logging.getLogger(__name__)

class BackgroundTasks:
    def __init__(self):
        self.is_running = False
        self.cleanup_interval = 24 * 60 * 60  # 24 часа в секундах

    async def start_cleanup_task(self):
        """Запускает фоновую задачу очистки логов"""
        if self.is_running:
            logger.warning("Фоновая задача очистки логов уже запущена")
            return

        self.is_running = True
        logger.info("Запуск фоновой задачи очистки логов")

        try:
            while self.is_running:
                try:
                    # Выполняем очистку
                    deleted_count = await LogCleaner.cleanup_old_logs(days_to_keep=30)
                    
                    if deleted_count > 0:
                        logger.info(f"Автоматическая очистка: удалено {deleted_count} старых логов")
                    
                    # Ждем до следующего выполнения
                    await asyncio.sleep(self.cleanup_interval)
                    
                except Exception as e:
                    logger.error(f"Ошибка в фоновой задаче очистки логов: {e}")
                    # Ждем перед повторной попыткой
                    await asyncio.sleep(3600)  # 1 час
                    
        except asyncio.CancelledError:
            logger.info("Фоновая задача очистки логов остановлена")
        finally:
            self.is_running = False

    def stop_cleanup_task(self):
        """Останавливает фоновую задачу"""
        self.is_running = False
        logger.info("Остановка фоновой задачи очистки логов")

# Глобальный экземпляр
background_tasks = BackgroundTasks()