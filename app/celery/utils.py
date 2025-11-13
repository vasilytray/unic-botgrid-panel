# app/celery/utils.py
import asyncio
import inspect
from app.database import async_session_maker

def run_async_method(async_func, *args, **kwargs):
    """
    Запуск async функции в синхронном контексте Celery
    """
    try:
        # Проверяем, является ли функция async
        if not inspect.iscoroutinefunction(async_func):
            # Если это не async функция, вызываем напрямую
            return async_func(*args, **kwargs)
        
        # Создаем новую event loop для каждого вызова
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(async_func(*args, **kwargs))
            return result
        finally:
            loop.close()
            
    except RuntimeError as e:
        # Если уже есть running loop (например, в тестах)
        if "cannot be called from a running event loop" in str(e):
            return asyncio.run(async_func(*args, **kwargs))
        raise e

def run_async_method_safe(async_func, *args, **kwargs):
    """
    Безопасный запуск async метода с обработкой ошибок
    """
    try:
        return run_async_method(async_func, *args, **kwargs)
    except Exception as e:
        # Логируем ошибку и возвращаем None или значение по умолчанию
        from loguru import logger
        logger.error(f"Error running async method {async_func.__name__}: {e}")
        return None