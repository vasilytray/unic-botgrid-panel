from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SRoles(BaseModel):
    id: int
    role_name: str = Field(..., description="Название Роли")
    role_description: Optional[str] = Field(None, description="Описание Роли")
    count_users: int = Field(0, description="Количество пользователей")

class SRolesAdd(BaseModel):
    role_name: str = Field(..., description="Название Роли")
    role_description: str = Field(None, description="Описание Роли")

class SRolesUpdDesc(BaseModel):
    role_name: str = Field(..., description="Название Роли")
    role_description: str = Field(None, description="Новое описание Роли")

class SRolesDelete(BaseModel):
    role_name: str = Field(..., description="Название роли для удаления")

class RoleStatItem(BaseModel):
    id: int
    name: str
    user_count: int
    is_admin_role: bool

class SRolesStats(BaseModel):
    total_roles: int
    total_users: int
    roles: List[RoleStatItem]