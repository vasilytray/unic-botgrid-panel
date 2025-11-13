# app/tasks/log_cleanup_task.py
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import delete, func, select
from app.database import async_session_maker
from app.users.models import UserLog
from app.logger import app_logger as logger

class LogCleanupTask:
    def __init__(self):
        self.is_running = False
        self.cleanup_days = 30
        self.interval_hours = 24
        self.last_run = None
        self.last_deleted_count = 0

    async def run_cleanup(self):
        """Однократная очистка старых логов"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.cleanup_days)
            
            async with async_session_maker() as session:
                async with session.begin():
                    # Сначала посчитаем сколько будет удалено
                    count_stmt = select(func.count(UserLog.id)).where(
                        UserLog.created_at < cutoff_date
                    )
                    count_result = await session.execute(count_stmt)
                    to_delete_count = count_result.scalar()
                    
                    # Выполняем удаление
                    stmt = delete(UserLog).where(UserLog.created_at < cutoff_date)
                    result = await session.execute(stmt)
                    deleted_count = result.rowcount
                    await session.commit()
                
                self.last_run = datetime.now()
                self.last_deleted_count = deleted_count
                
                if deleted_count > 0:
                    logger.info(f"✅ Очищено {deleted_count} записей логов старше {self.cleanup_days} дней")
                else:
                    logger.info("✅ Старые логи для очистки не найдены")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке логов: {e}")
            return 0

    async def start_periodic_cleanup(self):
        """Запуск периодической очистки"""
        self.is_running = True
        logger.info(f"🔄 Запуск периодической очистки логов (интервал: {self.interval_hours}ч)")
        
        # Сразу выполняем первую очистку
        await self.run_cleanup()
        
        while self.is_running:
            try:
                logger.info(f"⏰ Следующая очистка через {self.interval_hours} часов...")
                await asyncio.sleep(self.interval_hours * 3600)
                
                if self.is_running:  # Проверяем не остановили ли задачу
                    await self.run_cleanup()
                
            except asyncio.CancelledError:
                logger.info("⏹️  Задача очистки логов отменена")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в фоновой задаче очистки: {e}")
                await asyncio.sleep(3600)  # Ждем час перед повторной попыткой

    def stop(self):
        """Остановка задачи"""
        self.is_running = False
        logger.info("🛑 Остановка задачи очистки логов")

    def get_status(self):
        """Получение статуса задачи"""
        return {
            "is_running": self.is_running,
            "cleanup_days": self.cleanup_days,
            "interval_hours": self.interval_hours,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_deleted_count": self.last_deleted_count
        }

# Глобальный экземпляр
log_cleanup = LogCleanupTask()