from fastapi import APIRouter, Depends, HTTPException, status
from app.roles.dao import RolesDAO
from app.roles.schemas import SRolesAdd, SRolesUpdDesc, SRoles, SRolesDelete, SRolesStats
from app.users.dependencies import get_current_user, get_current_admin, get_current_super_admin

router = APIRouter(prefix='/roles', tags=['Работа с ролями'])

@router.get("/", summary="Список всех ролей", response_model=list[SRoles])
async def get_all_roles() -> list[SRoles]:
    """Получить список всех ролей (доступно всем аутентифицированным пользователям)"""
    return await RolesDAO.find_all_with_users_count()

@router.get("/stats/", summary="Статистика по ролям", response_model=SRolesStats)
async def get_roles_stats(admin_user = Depends(get_current_admin)) -> SRolesStats:
    """Получить статистику по ролям (только для админов)"""
    return await RolesDAO.get_role_stats()

@router.post("/add/", summary="Добавить новую роль")
async def add_role(
    role: SRolesAdd, 
    admin_user = Depends(get_current_admin)
) -> dict:
    """Добавить новую роль (только для админов)"""
    # Проверяем, существует ли роль с таким именем
    existing_role = await RolesDAO.find_by_name(role.role_name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Роль с именем "{role.role_name}" уже существует'
        )
    
    # Добавляем роль
    new_role = await RolesDAO.add(**role.model_dump())
    if new_role:
        return {
            "message": "Роль успешно добавлена!", 
            "role": role.role_name
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при добавлении роли!"
        )

@router.put("/update_description/", summary="Обновить описание роли")
async def update_role_description(
    role: SRolesUpdDesc, 
    admin_user = Depends(get_current_admin)
) -> dict:
    """Обновить описание роли (только для админов)"""
    check = await RolesDAO.update_role_description(role.role_name, role.role_description)
    if check:
        return {
            "message": "Описание роли успешно обновлено!", 
            "role": role.role_name
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Роль "{role.role_name}" не найдена!'
        )

@router.delete("/delete/", summary="Удалить роль")
async def delete_role(
    role_data: SRolesDelete, 
    admin_user = Depends(get_current_admin)
) -> dict:
    """Удалить роль (только для админов)"""
    try:
        # Запрещаем удаление системных ролей
        protected_roles = ["superadmin", "admin", "user", "moderator"]
        if role_data.role_name.lower() in protected_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя удалять системные роли"
            )
        
        success = await RolesDAO.delete_role_by_name(role_data.role_name)
        if success:
            return {
                "message": f"Роль '{role_data.role_name}' успешно удалена!"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Роль "{role_data.role_name}" не найдена!'
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/admin-roles/", summary="Список административных ролей")
async def get_admin_roles(super_admin = Depends(get_current_super_admin)) -> list[SRoles]:
    """Получить список только административных ролей (только для суперадмина)"""
    return await RolesDAO.get_admin_roles()