from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError
from typing import Optional
from datetime import datetime, timezone
from app.config import get_auth_data
from app.users.models import User
from app.exceptions import TokenExpiredException, NoJwtException, NoUserIdException, ForbiddenException, TokenNoFoundException
from app.users.dao import UsersDAO
from app.roles.models import Role, RoleTypes
from app.utils.secutils import SecurityUtils
from app.users.ip_dao import UserAllowedIPsDAO


def get_token(request: Request):
    token = request.cookies.get('users_access_token')
    if not token:
        raise TokenNoFoundException
    return token

  
async def get_current_user(token: str = Depends(get_token)):
    """
    Основная зависимость для получения текущего пользователя
    Используется для защищенных эндпоинтов
    """
    try:
        auth_data = get_auth_data()
        payload = jwt.decode(token, auth_data['secret_key'], algorithms=[auth_data['algorithm']])
    except JWTError:
        raise NoJwtException

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise TokenExpiredException

    user_id = payload.get('sub')
    if not user_id:
        raise NoUserIdException

    user = await UsersDAO.find_one_or_none_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Пользователь не найден')

    return user

async def get_optional_user(request: Request) -> Optional[User]:
    """
    Зависимость для опционального получения пользователя
    Возвращает пользователя если авторизован, иначе None
    Используется для главной страницы и публичных эндпоинтов
    """
    try:
        token = request.cookies.get('users_access_token')
        if not token:
            return None
            
        auth_data = get_auth_data()
        payload = jwt.decode(token, auth_data['secret_key'], algorithms=[auth_data['algorithm']])
        
        # Проверяем срок действия токена
        expire = payload.get('exp')
        if expire:
            expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
            if expire_time < datetime.now(timezone.utc):
                return None
        
        user_id = payload.get('sub')
        if not user_id:
            return None
            
        user = await UsersDAO.find_one_or_none_by_id(int(user_id))
        return user
        
    except (JWTError, Exception):
        # Любая ошибка - считаем пользователя неавторизованным
        return None

async def get_current_admin(current_user: User = Depends(get_current_user)):
    """Проверяет, что пользователь имеет роль Admin или SuperAdmin"""
    if current_user.is_admin:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Недостаточно прав!')

async def get_current_moderator(current_user: User = Depends(get_current_user)):
    """Проверяет, что пользователь имеет роль SuperAdmin"""
    if current_user.is_moderator:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Недостаточно прав!')

async def get_current_super_admin(current_user: User = Depends(get_current_user)):
    """Проверяет, что пользователь имеет роль SuperAdmin"""
    if current_user.is_super_admin:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail='Требуются права суперадминистратора!'
    )

async def validate_role_change(current_user: User, target_user_id: int, new_role_id: int):
    """
    Валидация изменения роли пользователя
    """
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
    target_user = await UsersDAO.find_one_or_none_by_id(target_user_id)
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

async def log_role_change(user_id: int, old_role_id: int, new_role_id: int, changed_by: int, description: str = None):
    """Создать запись в логе об изменении роли"""
    from app.roles.dao import RolesDAO
    from app.users.dao import UserLogsDAO
    
    old_role_name = await RolesDAO.get_role_name_by_id(old_role_id)
    new_role_name = await RolesDAO.get_role_name_by_id(new_role_id)
    
    log_data = {
        'user_id': user_id,
        'action_type': 'role_change',
        'old_value': f"role_id:{old_role_id}:{old_role_name}",
        'new_value': f"role_id:{new_role_id}:{new_role_name}",
        'description': description or f"Изменение роли с '{old_role_name}' на '{new_role_name}'",
        'changed_by': changed_by
    }
    
    await UserLogsDAO.create_log(**log_data)
    return log_data

async def update_role_counters(old_role_id: int, new_role_id: int):
    """Обновить счетчики пользователей в ролях"""
    from app.roles.models import Role
    
    if old_role_id and old_role_id != new_role_id:
        await Role.decrement_count(old_role_id)
    
    if new_role_id != old_role_id:
        await Role.increment_count(new_role_id)

async def validate_ip_access(request: Request, current_user: User = Depends(get_current_user)):
    """
    Проверяет доступ по IP адресу
    """
    client_ip = SecurityUtils.get_client_ip(request)
    
    # Проверяем ограничения по IP
    if not await SecurityUtils.is_ip_allowed(current_user.id, client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Доступ с IP {client_ip} запрещен"
        )
    
    return current_user

async def get_current_user_with_ip_check(
    request: Request, 
    token: str = Depends(get_token)
):
    """
    Основная зависимость с проверкой IP
    """
    user = await get_current_user(token)
    
    # Проверяем IP
    client_ip = SecurityUtils.get_client_ip(request)
    if not await SecurityUtils.is_ip_allowed(user.id, client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Доступ с IP {client_ip} запрещен"
        )
    
    return user