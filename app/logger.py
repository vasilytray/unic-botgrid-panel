import logging
import sys
from loguru import logger  # Рекомендую использовать loguru - очень удобно!

# Настройка intercept для стандартного logging
class InterceptHandler(logging.Handler):
    def emit(self, record):
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

def setup_logger():
    """Настройка логгера для приложения"""
    
    # Убираем стандартные обработчики
    logging.getLogger().handlers = []
    
    # Настраиваем loguru
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "level": "INFO",
                "colorize": True,
            },
            {
                "sink": "logs/app.log",
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                "level": "INFO",
                "rotation": "10 MB",  # Ротация логов по размеру
                "retention": "30 days",  # Хранение логов 30 дней
                "compression": "zip"  # Сжатие старых логов
            }
        ]
    )
    
    # Перехватываем логи стандартной библиотеки
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    return logger

# Глобальный логгер
app_logger = setup_logger()