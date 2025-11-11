# app/services/schemas.py
from pydantic import BaseModel
from datetime import datetime
from app.services.models import ServiceType, ServiceStatus
from typing import Optional, Dict, Any, List

class ServiceBase(BaseModel):
    name: str
    service_type: ServiceType
    cpu_cores: int = 1
    memory_mb: int = 1024
    storage_gb: int = 20

class ServiceCreate(ServiceBase):
    image_name: Optional[str] = None
    environment_vars: Dict[str, Any] = {}
    port_mappings: Dict[str, str] = {}
    docker_command: Optional[str] = None

# Добавляем недостающую схему ServiceUpdate
class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_mb: Optional[int] = None
    storage_gb: Optional[int] = None
    status: Optional[ServiceStatus] = None

class ServiceResponse(ServiceBase):
    id: int
    status: ServiceStatus
    ip_address: Optional[str]
    image_name: Optional[str]
    environment_vars: Dict[str, Any] = {}
    port_mappings: Dict[str, str] = {}
    created_at: datetime
    updated_at: datetime
    last_health_check: Optional[datetime]
    
    class Config:
        from_attributes = True

class BillingPlanBase(BaseModel):
    name: str
    service_type: ServiceType
    price_monthly: float
    cpu_cores: int
    memory_mb: int
    storage_gb: int
    bandwidth_gb: Optional[int] = None
    description: Optional[str] = None

class BillingPlanCreate(BillingPlanBase):
    pass

class BillingPlanResponse(BillingPlanBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Добавляем схему для списка сервисов
class ServiceListResponse(BaseModel):
    services: List[ServiceResponse]
    total: int
    
    class Config:
        from_attributes = True