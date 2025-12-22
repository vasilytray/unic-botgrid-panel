# app/services/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import async_session_maker
from app.services.models import Service, ServiceType, ServiceStatus, BillingPlan
from app.services.schemas import (
    ServiceCreate, ServiceResponse, ServiceUpdate, 
    BillingPlanCreate, BillingPlanResponse, ServiceListResponse
)
from app.users.dependencies import get_current_user, get_current_admin
from app.users.models import User

router = APIRouter(prefix="/services", tags=["Services"])

@router.get("/", response_model=List[ServiceResponse])
async def get_my_services(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_session_maker)
):
    """Получить все сервисы пользователя"""
    # pass
    """Получить все сервисы пользователя"""
    # Временная заглушка
    return ServiceListResponse(services=[], total=0)

@router.post("/", response_model=ServiceResponse)
async def create_service(
    # service_data: ServiceCreate,  # Временно закомментируем
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_session_maker)
):
    """Создать новый сервис (VPS, Docker и т.д.)"""
    # Временная заглушка
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Функционал создания сервисов временно недоступен"
    )

@router.post("/vps", response_model=ServiceResponse)
async def create_vps(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_session_maker)
):
    """Создать VPS сервер"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Функционал создания VPS временно недоступен"
    )

@router.post("/docker", response_model=ServiceResponse)
async def create_docker_container(
    # service_data: ServiceCreate,  # Временно закомментируем
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_session_maker)
):
    """Создать Docker контейнер"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Функционал создания Docker контейнеров временно недоступен"
    )

@router.post("/n8n", response_model=ServiceResponse)
async def create_n8n_instance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_session_maker)
):
    """Создать n8n инстанс"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Функционал создания n8n инстансов временно недоступен"
    )

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_session_maker)
):
    """Получить информацию о сервисе"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Сервис с ID {service_id} не найден"
    )

@router.post("/{service_id}/start")
async def start_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_session_maker)
):
    """Запустить сервис"""
    # Временная заглушка - всегда успех для тестирования
    return {"message": f"Сервис {service_id} запущен", "status": "success"}

@router.post("/{service_id}/stop")
async def stop_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_session_maker)
):
    """Остановить сервис"""
    # Временная заглушка - всегда успех для тестирования
    return {"message": f"Сервис {service_id} остановлен", "status": "success"}

@router.post("/{service_id}/restart")
async def restart_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_session_maker)
):
    """Перезапустить сервис"""
    # Временная заглушка - всегда успех для тестирования
    return {"message": f"Сервис {service_id} перезапущен", "status": "success"}

@router.delete("/{service_id}")
async def delete_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_session_maker)
):
    """Удалить сервис"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Функционал удаления сервисов временно недоступен"
    )

# Админские эндпоинты
@router.get("/admin/plans/", response_model=List)  # Временно убрали BillingPlanResponse
async def get_billing_plans(
    current_user: User = Depends(get_current_user),  # Временно убрали get_current_admin_user
    db: AsyncSession = Depends(async_session_maker)
):
    """Получить все тарифные планы"""
    # Временная заглушка
    return []