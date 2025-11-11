# app/roles/dependencies.py
from fastapi import Depends, HTTPException, status
from app.users.dependencies import get_current_user
from app.users.models import User
from app.roles.models import RoleTypes

def require_roles(required_roles: list[RoleTypes]):
    """Зависимость для проверки ролей пользователя"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role_id not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к этому ресурсу"
            )
        return current_user
    return role_checker

# Альтернативная версия если RoleTypes - это класс с константами
def require_roles_list(required_role_ids: list[int]):
    """Зависимость для проверки ролей по ID"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role_id not in required_role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к этому ресурсу"
            )
        return current_user
    return role_checker

# Специфичные проверки для разных уровней доступа
def require_admin_access():
    """Только для админов, модераторов и суперадминов"""
    return require_roles([RoleTypes.SUPER_ADMIN, RoleTypes.ADMIN, RoleTypes.MODERATOR])

def require_moderator_access():
    """Только для модераторов и выше"""
    return require_roles([RoleTypes.SUPER_ADMIN, RoleTypes.ADMIN, RoleTypes.MODERATOR])

def require_super_admin_access():
    """Только для суперадминов"""
    return require_roles([RoleTypes.SUPER_ADMIN])