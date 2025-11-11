import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import delete
from app.database import async_session_maker
from app.users.models import UserLog

logger = logging.getLogger(__name__)

class LogCleaner:
    @staticmethod
    async def cleanup_old_logs(days_to_keep: int = 30):
        """
        Удаляет логи старше указанного количества дней
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            async with async_session_maker() as session:
                async with session.begin():
                    # Удаляем логи старше cutoff_date
                    stmt = delete(UserLog).where(
                        UserLog.created_at < cutoff_date
                    )
                    result = await session.execute(stmt)
                    deleted_count = result.rowcount
                    
                    await session.commit()
                    
                    logger.info(f"Удалено {deleted_count} записей логов старше {days_to_keep} дней")
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"Ошибка при очистке логов: {e}")
            await session.rollback()
            raise e

    @staticmethod
    async def get_log_statistics():
        """
        Получает статистику по логам
        """
        try:
            async with async_session_maker() as session:
                from sqlalchemy import func, select
                
                # Общее количество логов
                total_count_query = select(func.count(UserLog.id))
                total_result = await session.execute(total_count_query)
                total_count = total_result.scalar()
                
                # Количество логов старше 30 дней
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
                old_count_query = select(func.count(UserLog.id)).where(
                    UserLog.created_at < cutoff_date
                )
                old_result = await session.execute(old_count_query)
                old_count = old_result.scalar()
                
                # Самые старые и новые логи
                oldest_query = select(func.min(UserLog.created_at))
                newest_query = select(func.max(UserLog.created_at))
                
                oldest_result = await session.execute(oldest_query)
                newest_result = await session.execute(newest_query)
                
                oldest_date = oldest_result.scalar()
                newest_date = newest_result.scalar()
                
                return {
                    "total_logs": total_count,
                    "old_logs_30_days": old_count,
                    "oldest_log_date": oldest_date,
                    "newest_log_date": newest_date
                }
                
        except Exception as e:
            logger.error(f"Ошибка при получении статистики логов: {e}")
            return {}