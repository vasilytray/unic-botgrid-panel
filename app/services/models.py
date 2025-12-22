# app/services/models.py
from sqlalchemy import String, Text, Float, Integer, Boolean, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from typing import List, Optional, Dict, Any

from app.core.database import Base, int_pk, created_at, updated_at, datetime_null_true, bool_default_false, int_default_zero, float_default_zero
from app.users.models import User

class ServiceType(str, Enum):
    VPS = "vps"
    DOCKER = "docker"
    BOT = "bot"
    N8N = "n8n"
    DATABASE = "database"

class ServiceStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    STOPPED = "stopped"
    ERROR = "error"

class Service(Base):
    __tablename__ = "services"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_type: Mapped[ServiceType] = mapped_column(SQLEnum(ServiceType))
    status: Mapped[ServiceStatus] = mapped_column(SQLEnum(ServiceStatus), default=ServiceStatus.PENDING)
    
    # Конфигурация сервиса
    cpu_cores: Mapped[int] = mapped_column(default=1)
    memory_mb: Mapped[int] = mapped_column(default=1024)
    storage_gb: Mapped[int] = mapped_column(default=20)
    
    # Сетевые настройки
    ip_address: Mapped[Optional[str]] = mapped_column(nullable=True)
    port_mappings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Docker специфичные поля
    image_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    environment_vars: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    docker_command: Mapped[Optional[str]] = mapped_column(nullable=True)
    
    # ДОБАВЛЯЕМ СВЯЗЬ С ПОЛЬЗОВАТЕЛЕМ
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="services")
    
    # Мониторинг
    last_health_check: Mapped[datetime_null_true]
    usage_stats: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Дополнительные поля
    is_active: Mapped[bool] = mapped_column(default=True)
    monthly_price: Mapped[float] = mapped_column(default=0.0)

class BillingPlan(Base):
    __tablename__ = "billing_plans"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    service_type: Mapped[ServiceType] = mapped_column(SQLEnum(ServiceType))
    price_monthly: Mapped[float] = mapped_column(nullable=False)
    cpu_cores: Mapped[int] = mapped_column(nullable=False)
    memory_mb: Mapped[int] = mapped_column(nullable=False)
    storage_gb: Mapped[int] = mapped_column(nullable=False)
    bandwidth_gb: Mapped[Optional[int]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)