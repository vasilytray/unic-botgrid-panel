# app/core/exceptions.py
from fastapi import HTTPException, status
from typing import Optional, Any, Dict

class BaseServiceException(HTTPException):
    """Базовое исключение для всех кастомных исключений сервиса"""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

# Аутентификация и авторизация
class TokenExpiredException(BaseServiceException):
    def __init__(self, detail: str = "Токен истек"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

class TokenNotFoundException(BaseServiceException):
    def __init__(self, detail: str = "Токен не найден"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

class InvalidTokenException(BaseServiceException):
    def __init__(self, detail: str = "Токен не валидный"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

class NoUserIdException(BaseServiceException):
    def __init__(self, detail: str = "Не найден ID пользователя"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

class InvalidCredentialsException(BaseServiceException):
    def __init__(self, detail: str = "Неверная почта или пароль"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

# Пользователи
class UserAlreadyExistsException(BaseServiceException):
    def __init__(self, detail: str = "Пользователь уже существует"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

class UserNotFoundException(BaseServiceException):
    def __init__(self, user_id: Optional[str] = None):
        detail = f"Пользователь с id {user_id} не найден" if user_id else "Пользователь не найден"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class PasswordMismatchException(BaseServiceException):
    def __init__(self, detail: str = "Пароли не совпадают"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

# Права доступа
class InsufficientPermissionsException(BaseServiceException):
    def __init__(self, detail: str = "Недостаточно прав"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class ForbiddenException(BaseServiceException):
    def __init__(self, detail: str = "Доступ запрещен"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

# Валидация данных
class ValidationException(BaseServiceException):
    def __init__(self, detail: str = "Ошибка валидации данных"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

# Ресурсы
class ResourceNotFoundException(BaseServiceException):
    def __init__(self, resource: str = "ресурс", resource_id: Optional[str] = None):
        detail = f"{resource} не найден"
        if resource_id:
            detail = f"{resource} с id {resource_id} не найден"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class ResourceAlreadyExistsException(BaseServiceException):
    def __init__(self, resource: str = "ресурс", detail: Optional[str] = None):
        if not detail:
            detail = f"{resource} уже существует"
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

# Внешние сервисы
class ExternalServiceException(BaseServiceException):
    def __init__(self, service: str = "внешний сервис", detail: Optional[str] = None):
        if not detail:
            detail = f"Ошибка при обращении к {service}"
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )

class RedisConnectionException(ExternalServiceException):
    def __init__(self, detail: str = "Ошибка подключения к Redis"):
        super().__init__(service="Redis", detail=detail)

class DatabaseConnectionException(ExternalServiceException):
    def __init__(self, detail: str = "Ошибка подключения к базе данных"):
        super().__init__(service="базе данных", detail=detail)

class RabbitMQConnectionException(ExternalServiceException):
    def __init__(self, detail: str = "Ошибка подключения к RabbitMQ"):
        super().__init__(service="RabbitMQ", detail=detail)

# Контейнеры и деплой
class ContainerDeploymentException(BaseServiceException):
    def __init__(self, detail: str = "Ошибка деплоя контейнера"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

class ContainerNotFoundException(BaseServiceException):
    def __init__(self, container_id: Optional[str] = None):
        detail = f"Контейнер с id {container_id} не найден" if container_id else "Контейнер не найден"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

# Для обратной совместимости (можно постепенно убрать)
IncorrectEmailOrPasswordException = InvalidCredentialsException()
TokenNoFound = TokenNotFoundException()
NoJwtException = InvalidTokenException()