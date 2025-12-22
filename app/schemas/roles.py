# app/schemas/roles.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class RoleBase(BaseModel):
    role_name: str = Field(..., min_length=2, max_length=50, description="Название роли")
    role_description: Optional[str] = Field(None, description="Описание роли")

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    role_name: Optional[str] = Field(None, min_length=2, max_length=50, description="Название роли")

class RoleResponse(RoleBase):
    id: int
    count_users: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Ранее known_as from_orm

class RoleListResponse(BaseModel):
    roles: list[RoleResponse]
    total: int

class RoleWithUsersResponse(RoleResponse):
    users_count: int = Field(..., description="Количество пользователей с этой ролью")

class RoleSimpleResponse(BaseModel):
    id: int
    role_name: str
    count_users: int

    class Config:
        from_attributes = True
