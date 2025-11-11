from datetime import datetime, timezone
from typing import Optional

class DateTimeUtils:
    @staticmethod
    def get_current_utc_datetime() -> datetime:
        """Получить текущее UTC время без временной зоны (для PostgreSQL)"""
        return datetime.now(timezone.utc).replace(tzinfo=None)
    
    @staticmethod
    def to_naive_utc(dt: datetime) -> datetime:
        """Преобразовать datetime в наивный UTC (без временной зоны)"""
        if dt.tzinfo is not None:
            # Конвертируем в UTC и убираем временную зону
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    
    @staticmethod
    def ensure_naive_utc(dt: Optional[datetime] = None) -> datetime:
        """Гарантировать, что возвращается наивный UTC datetime"""
        if dt is None:
            return DateTimeUtils.get_current_utc_datetime()
        return DateTimeUtils.to_naive_utc(dt)