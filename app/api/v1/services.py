# app/api/v1/services.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.core.dependencies import get_current_user
from app.models.users import User
from app.workers.container_worker import ContainerDeployRequest
from app.utils.broker_utils import broker_manager
from loguru import logger

router = APIRouter(prefix="/services", tags=["services"])

@router.post("/deploy-container")
async def deploy_container(
    deploy_request: ContainerDeployRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Запуск деплоя контейнера через FastStream"""
    
    async def publish_deploy_task():
        success = await broker_manager.publish_message(
            deploy_request.model_dump(),
            "container.deploy"
        )
        if success:
            logger.info(f"Deploy task published for user {current_user.id}")
        else:
            logger.error(f"Failed to publish deploy task for user {current_user.id}")
    
    # Запускаем в фоне
    background_tasks.add_task(publish_deploy_task)
    
    return {
        "message": "Container deployment started", 
        "status": "processing",
        "user_id": current_user.id
    }

@router.post("/stop-container")
async def stop_container(
    container_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Остановка контейнера"""
    
    async def publish_stop_task():
        success = await broker_manager.publish_message(
            {
                "container_id": container_id,
                "user_id": current_user.id,
                "action": "stop"
            },
            "container.management"
        )
        if success:
            logger.info(f"Stop task published for container {container_id}")
    
    background_tasks.add_task(publish_stop_task)
    
    return {
        "message": "Container stop requested",
        "container_id": container_id,
        "status": "processing"
    }