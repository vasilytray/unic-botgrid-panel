# app/tickets/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class TicketMessageBase(BaseModel):
    message_text: str

class TicketMessageCreate(TicketMessageBase):
    pass

class TicketMessageResponse(TicketMessageBase):
    id: int
    ticket_id: int
    sender_id: int
    sender_name: str
    # sender_email: str  # Добавляем email для проверки роли
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TicketBase(BaseModel):
    subject: str
    description: str
    priority: str = "Medium"

class TicketCreate(TicketBase):
    pass

# Упрощенная схема для списков (без сообщений)
class TicketShortResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    user_nick: str = "User" # Добавляем user_nick
    subject: str
    status: str
    priority: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

# Детальная схема с сообщениями
class TicketDetailResponse(TicketShortResponse):
    messages: List[TicketMessageResponse] = []
    # first_message_text: Optional[str] = None  # Добавляем поле для первого сообщения
    first_message_id: Optional[int] = None  # ID первого сообщения

    model_config = ConfigDict(from_attributes=True)

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    is_pinned: Optional[bool] = None

class TicketListResponse(BaseModel):
    tickets: List[TicketShortResponse]  # Используем короткую версию для списков
    total_count: int
    page: int
    page_size: int
    total_pages: int