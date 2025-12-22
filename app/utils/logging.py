# app/utils/logging.py
import sys
import logging
from loguru import logger
from app.core.config import get_settings

settings = get_settings()

class InterceptHandler(logging.Handler):
    """
    Перехватчик логов стандартной библиотеки logging для перенаправления в loguru
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        # Получаем соответствующий уровень loguru
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Находим caller для корректного отображения
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging():
    """
    Настройка системы логирования для приложения
    """
    # Убираем стандартные обработчики
    logging.getLogger().handlers = []
    
    # Настройка формата логов
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Конфигурация loguru
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "format": log_format,
                "level": settings.log_level,
                "colorize": True,
                "backtrace": settings.debug,  # Backtrace только в debug режиме
                "diagnose": settings.debug,   # Диагностика только в debug режиме
            },
            {
                "sink": "logs/app.log",
                "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
                "level": "INFO",
                "rotation": "10 MB",           # Ротация логов по размеру
                "retention": "30 days",        # Хранение логов 30 дней
                "compression": "zip",          # Сжатие старых логов
                "backtrace": True,
                "diagnose": True,
            },
            # Лог ошибок в отдельный файл
            {
                "sink": "logs/error.log", 
                "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
                "level": "ERROR",
                "rotation": "10 MB",
                "retention": "60 days",        # Ошибки храним дольше
                "compression": "zip",
                "backtrace": True,
                "diagnose": True,
            }
        ]
    )
    
    # Перехватываем логи стандартной библиотеки
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Устанавливаем уровень логирования для внешних библиотек
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
    logging.getLogger("fastapi").handlers = [InterceptHandler()]
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    
    logger.info(f"✅ Logging system initialized - Level: {settings.log_level}")

# Глобальный логгер для импорта
app_logger = logger

def get_logger(name: str):
    """
    Получить именованный логгер
    
    Args:
        name: Имя логгера (обычно __name__)
    
    Returns:
        Logger instance
    """
    return logger.bind(name=name)