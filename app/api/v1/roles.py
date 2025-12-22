# app/api/v1/roles.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.core.dependencies import get_current_super_admin, get_current_admin
from app.dao.roles import RoleDAO
from app.models.users import User
from app.schemas.roles import (
    RoleCreate, RoleResponse, RoleListResponse, 
    RoleUpdate, RoleWithUsersResponse, RoleSimpleResponse
)

router = APIRouter(prefix="/roles", tags=["Работа с ролями"])

@router.get("/", summary="Список всех ролей", response_model=RoleListResponse)
async def get_all_roles(
    current_user: User = Depends(get_current_admin)
):
    """Получить все роли (только для админов)"""
    role_dao = RoleDAO()
    roles = await role_dao.get_all_roles()
    
    # Преобразуем модели Role в схемы RoleResponse используя model_validate
    role_responses = [
        RoleResponse.model_validate({
            "id": role.id,
            "role_name": role.role_name,
            "role_description": role.role_description,
            "count_users": role.count_users,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        })
        for role in roles
    ]

@router.get("/available", response_model=List[RoleSimpleResponse])
async def get_available_roles(
    exclude_super_admin: bool = True,
    current_user: User = Depends(get_current_admin)
):
    """Получить роли доступные для назначения"""
    role_dao = RoleDAO()
    roles = await role_dao.get_available_roles(exclude_super_admin=exclude_super_admin)
    return roles

@router.get("/{role_id}", response_model=RoleWithUsersResponse)
async def get_role_by_id(
    role_id: int,
    current_user: User = Depends(get_current_admin)
):
    """Получить роль по ID (только для админов)"""
    role_dao = RoleDAO()
    role = await role_dao.get_role_by_id(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Роль с ID {role_id} не найдена"
        )
    
    return RoleWithUsersResponse(
        id=role.id,
        role_name=role.role_name,
        role_description=role.role_description,
        count_users=role.count_users,
        users_count=role.count_users,
        created_at=role.created_at,
        updated_at=role.updated_at
    )

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_super_admin)
):
    """Создать новую роль (только для суперадмина)"""
    role_dao = RoleDAO()
    
    # Проверяем существование роли с таким именем
    existing_role = await role_dao.get_role_by_name(role_data.role_name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Роль с таким именем уже существует"
        )
    
    # Создаем роль
    role = await role_dao.create_role(
        role_name=role_data.role_name,
        role_description=role_data.role_description
    )
    
    return RoleResponse.model_validate(role)

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_super_admin)
):
    """Обновить роль (только для суперадмина)"""
    role_dao = RoleDAO()
    
    # Проверяем существование роли
    existing_role = await role_dao.get_role_by_id(role_id)
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Роль с ID {role_id} не найдена"
        )
    
    # Проверяем уникальность имени, если оно изменяется
    if role_data.role_name and role_data.role_name != existing_role.role_name:
        role_with_same_name = await role_dao.get_role_by_name(role_data.role_name)
        if role_with_same_name and role_with_same_name.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Роль с таким именем уже существует"
            )
    
    # Подготавливаем данные для обновления
    update_data = {}
    if role_data.role_name is not None:
        update_data['role_name'] = role_data.role_name
    if role_data.role_description is not None:
        update_data['role_description'] = role_data.role_description
    
    # Обновляем роль
    success = await role_dao.update_role_data(role_id, **update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении роли"
        )
    
    # Получаем обновленную роль
    updated_role = await role_dao.get_role_by_id(role_id)
    return RoleResponse.model_validate(updated_role)

@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_super_admin)
):
    """Удалить роль (только для суперадмина)"""
    role_dao = RoleDAO()
    
    # Проверяем существование роли
    existing_role = await role_dao.get_role_by_id(role_id)
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Роль с ID {role_id} не найдена"
        )
    
    # Нельзя удалить системные роли
    if role_id in [1, 2, 3, 4]:  # SUPER_ADMIN, ADMIN, MODERATOR, USER
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить системную роль"
        )
    
    # Проверяем, что у роли нет пользователей
    if existing_role.count_users > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить роль, у которой есть пользователи"
        )
    
    # Удаляем роль
    success = await role_dao.delete(id=role_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении роли"
        )
    
    return {"message": f"Роль '{existing_role.role_name}' успешно удалена"}