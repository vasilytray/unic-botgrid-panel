# app/core/dependencies.py (дополняем)
from fastapi import Request, Depends, HTTPException, status
from jose import jwt, JWTError
from typing import Optional
from datetime import datetime, timezone

from app.core.database import async_session_maker
from app.core.config import get_settings
from app.dao.users import UserDAO, UserLogsDAO
# from app.dao.tickets import TicketDAO
from app.dao.roles import RoleDAO
from app.models.users import User
from app.models.roles import Role, RoleTypes
from app.utils.secutils import SecurityUtils
from app.dao.redis import redis_dao
from app.services.notification_service import notification_service, centrifugo_service

settings=get_settings() 

# DAO dependencies
async def get_user_dao() -> UserDAO:
    return UserDAO()

async def get_user_logs_dao() -> UserLogsDAO:
    return UserLogsDAO()

# Добавляем DAO зависимости для ролей
async def get_role_dao() -> RoleDAO:
    return RoleDAO()

async def get_redis_dao():
    return redis_dao

# Authentication dependencies
def get_token(request: Request):
    token = request.cookies.get('users_access_token')
    if not token:
        from app.core.exceptions import TokenNotFoundException
        raise TokenNotFoundException
    return token

async def get_current_user(
    token: str = Depends(get_token),
    user_dao: UserDAO = Depends(get_user_dao)
) -> User:
    """Основная зависимость для получения текущего пользователя"""
   
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        from app.core.exceptions import NoJwtException
        raise NoJwtException

    expire = payload.get('exp')
    if expire:
        expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
        if expire_time < datetime.now(timezone.utc):
            from app.core.exceptions import TokenExpiredException
            raise TokenExpiredException

    user_id = payload.get('sub')
    if not user_id:
        from app.core.exceptions import NoUserIdException
        raise NoUserIdException

    user = await user_dao.get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Пользователь не найден'
        )

    return user

async def get_current_user_with_ip_check(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    """Зависимость с проверкой IP"""
    client_ip = SecurityUtils.get_client_ip(request)
    
    if not await SecurityUtils.is_ip_allowed(current_user.id, client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Доступ с IP {client_ip} запрещен"
        )
    
    return current_user

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, что пользователь имеет роль Admin или SuperAdmin"""
    if current_user.is_admin:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail='Недостаточно прав!'
    )

async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, что пользователь имеет роль SuperAdmin"""
    if current_user.is_super_admin:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail='Требуются права суперадминистратора!'
    )

# Validation dependencies
async def validate_role_change(
    current_user: User, 
    target_user_id: int, 
    new_role_id: int
):
    """Валидация изменения роли пользователя"""
    user_dao = UserDAO()
    
    # Суперадмин не может изменить свою роль
    if current_user.id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы не можете изменить свою собственную роль"
        )
    
    # Нельзя назначить роль суперадмина
    if new_role_id == RoleTypes.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя назначить роль суперадминистратора"
        )
    
    # Получаем информацию о целевом пользователе
    target_user = await user_dao.get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Нельзя изменять роль другого суперадмина
    if target_user.role_id == RoleTypes.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя изменять роль другого суперадминистратора"
        )
    
    return target_user

async def log_role_change(
    user_id: int, 
    old_role_id: int, 
    new_role_id: int, 
    changed_by: int, 
    description: Optional[str] = None,
    role_dao: RoleDAO = Depends(get_role_dao),
    user_logs_dao: UserLogsDAO = Depends(get_user_logs_dao)
):
    """Создать запись в логе об изменении роли"""
    
    # role_dao = RoleDAO()
    # user_logs_dao = UserLogsDAO()
    
    old_role_name = await role_dao.get_role_name_by_id(old_role_id)
    new_role_name = await role_dao.get_role_name_by_id(new_role_id)
    
    log_description = description or f"Изменение роли с '{old_role_name}' на '{new_role_name}'"
    
    log_data = {
        'user_id': user_id,
        'action_type': 'role_change',
        'old_value': f"role_id:{old_role_id}:{old_role_name}",
        'new_value': f"role_id:{new_role_id}:{new_role_name}",
        'description': log_description, 
        'changed_by': changed_by
    }
    
    await user_logs_dao.create_user_log(**log_data)
    return log_data

# Service dependencies

async def get_notification_service():
    """Зависимость для NotificationService"""
    return notification_service

async def get_centrifugo_service():
    """Зависимость для CentrifugoService"""
    return centrifugo_service