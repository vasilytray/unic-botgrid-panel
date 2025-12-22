# app/tickets/router.py
from fastapi import APIRouter, Request, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from app.core.database import async_session_maker
from sqlalchemy import func, select, text
from sqlalchemy.orm import joinedload, selectinload
from app.tickets.models import Ticket, TicketMessage

from app.tickets.dao import TicketDAO, TicketMessageDAO
from app.tickets.schemas import (
    TicketCreate, TicketShortResponse, TicketUpdate, 
    TicketMessageCreate, TicketListResponse, TicketDetailResponse,
    TicketMessageResponse
)
from app.tickets.models import TicketStatus, TicketPriority
from app.users.dependencies import get_current_user
from app.users.models import User
from app.roles.dependencies import require_roles_list, require_roles
from app.roles.models import RoleTypes

router = APIRouter(prefix='/tickets', tags=['Тикеты'])
templates = Jinja2Templates(directory='app/templates')

# Вспомогательные зависимости для проверки прав
async def get_ticket_with_access_check(ticket_id: int, current_user: User):
    """Получить тикет с проверкой прав доступа"""
    from app.roles.models import RoleTypes
    
    # Админы/модераторы имеют доступ ко всем тикетам
    if current_user.role_id in [RoleTypes.MODERATOR, RoleTypes.ADMIN, RoleTypes.SUPER_ADMIN]:
        ticket_data = await TicketDAO.get_ticket_detail(ticket_id)
    else:
        # Обычные пользователи - только к своим тикетам
        ticket_data = await TicketDAO.get_ticket_detail(ticket_id, user_id=current_user.id)
    
    if not ticket_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тикет не найден или у вас нет прав доступа"
        )
    
    return ticket_data

# Роуты для пользовательского интерфейса
@router.get("", response_class=HTMLResponse)
async def ticket_page(request: Request):
    """Главная страница тикет-системы"""
    return templates.TemplateResponse("ticket.html", {"request": request})

@router.get("/user", response_class=HTMLResponse)
async def user_tickets_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Страница тикетов пользователя"""
    return templates.TemplateResponse("ticket.html", {
        "request": request,
        "current_user": current_user,
        "user_authenticated": True
    })

@router.get("/admin", response_class=HTMLResponse)
async def admin_tickets_page(
    request: Request,
    current_user: User = Depends(require_roles([RoleTypes.MODERATOR, RoleTypes.ADMIN, RoleTypes.SUPER_ADMIN]))
):
    """Админская страница тикетов"""
    return templates.TemplateResponse("ticket.html", {
        "request": request,
        "current_user": current_user,
        "user_authenticated": True,
        "is_admin": True
    })

# API роуты
# 1. Статические роуты (без параметров)

@router.get("/api/tickets/stats")
async def get_ticket_stats(current_user: User = Depends(get_current_user)):
    """Получить статистику по тикетам"""
    if current_user.role_id in [RoleTypes.MODERATOR, RoleTypes.ADMIN, RoleTypes.SUPER_ADMIN]:
        # Админы видят общую статистику
        stats = await TicketDAO.get_ticket_stats()
    else:
        # Пользователи видят только свою статистику
        stats = await TicketDAO.get_ticket_stats(user_id=current_user.id)
    
    return stats

@router.post("/api/tickets", response_model=TicketDetailResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_user)
):
    """Создать новый тикет"""
    async with async_session_maker() as session:
        try:
            # Создаем тикет
            ticket = Ticket(
                user_id=current_user.id,
                subject=ticket_data.subject,
                description=ticket_data.description,
                priority=ticket_data.priority,
                status=TicketStatus.OPEN
            )
            session.add(ticket)
            await session.flush()  # Получаем ID
            
            # Создаем первое сообщение
            message = TicketMessage(
                ticket_id=ticket.id,
                sender_id=current_user.id,
                message_text=ticket_data.description
            )
            session.add(message)
            
            await session.commit()
            
            # Получаем созданный тикет с базовой информацией
            await session.refresh(ticket)
            
            # Загружаем пользователя для email
            user_query = select(User).where(User.id == current_user.id)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            # Загружаем сообщения
            messages_query = (
                select(TicketMessage)
                .options(joinedload(TicketMessage.sender))
                .where(TicketMessage.ticket_id == ticket.id)
                .order_by(TicketMessage.created_at)
            )
            messages_result = await session.execute(messages_query)
            messages = messages_result.unique().scalars().all()
            
            # Преобразуем в схему ответа
            return TicketDetailResponse(
                id=ticket.id,
                user_id=ticket.user_id,
                user_email=user.user_email if user else "Unknown",
                subject=ticket.subject,
                description=ticket.description,
                status=ticket.status,
                priority=ticket.priority,
                is_pinned=ticket.is_pinned,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
                message_count=len(messages),
                messages=[
                    TicketMessageResponse(
                        id=msg.id,
                        ticket_id=msg.ticket_id,
                        sender_id=msg.sender_id,
                        sender_name=msg.sender.user_email if msg.sender else "Unknown",
                        message_text=msg.message_text,
                        created_at=msg.created_at
                    ) for msg in messages
                ]
            )
            
        except Exception as e:
            await session.rollback()
            print(f"Ошибка создания тикета: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании тикета: {str(e)}"
            )

# 2. Роуты с префиксами

@router.get("/api/user/tickets", response_model=TicketListResponse)
async def get_user_tickets(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None)
):
    """Получить тикеты текущего пользователя"""
    result = await TicketDAO.get_user_tickets(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status
    )
    return result

@router.get("/api/admin/tickets", response_model=TicketListResponse)
async def get_admin_tickets(
    current_user: User = Depends(require_roles([RoleTypes.MODERATOR, RoleTypes.ADMIN, RoleTypes.SUPER_ADMIN])),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None)
):
    """Получить все тикеты (для админов)"""
    result = await TicketDAO.get_admin_tickets(
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        user_id=user_id
    )
    return result

# 3. Роуты с динамическими параметрами (в конце)

@router.get("/api/tickets/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user)
):
    """Получить тикет по ID с полной перепиской"""
    ticket_data = await get_ticket_with_access_check(ticket_id, current_user)
    
    ticket = ticket_data['ticket']
    user = ticket_data['user']
    messages = ticket_data['messages']
    first_message = ticket_data.get('first_message')
    
    # Используем первое сообщение как описание проблемы
    problem_description = first_message.message_text if first_message else ticket.description
    
    # Получаем user_nick безопасным способом
    user_nick = getattr(user, 'user_nick', None)
    if not user_nick:
        user_nick = user.user_email.split('@')[0] if user else "User"
    
    # Преобразуем в схему ответа
    return TicketDetailResponse(
        id=ticket.id,
        user_id=ticket.user_id,
        user_email=user.user_email if user else "Unknown",
        user_nick=user_nick,
        subject=ticket.subject,
        description=problem_description,
        status=ticket.status,
        priority=ticket.priority,
        is_pinned=ticket.is_pinned,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        message_count=len(messages),
        first_message_id=first_message.id if first_message else None,
        messages=[
            TicketMessageResponse(
                id=msg.id,
                ticket_id=msg.ticket_id,
                sender_id=msg.sender_id,
                sender_name=getattr(msg.sender, 'user_nick', msg.sender.user_email if msg.sender else "User"),
                message_text=msg.message_text,
                created_at=msg.created_at
            ) for msg in messages
        ]
    )

@router.put("/api/tickets/{ticket_id}", response_model=TicketDetailResponse)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    current_user: User = Depends(get_current_user)
):
    """Обновить тикет и вернуть полные данные с перепиской"""
    # Сначала проверяем права доступа
    ticket_data = await get_ticket_with_access_check(ticket_id, current_user)
    
    # Обновляем тикет
    await TicketDAO.update({"id": ticket_id}, **ticket_update.model_dump(exclude_unset=True))
    
    # Получаем обновленный тикет с перепиской
    updated_ticket_data = await get_ticket_with_access_check(ticket_id, current_user)
    
    ticket = updated_ticket_data['ticket']
    user = updated_ticket_data['user']
    messages = updated_ticket_data['messages']
    
    # Преобразуем в схему ответа
    return TicketDetailResponse(
        id=ticket.id,
        user_id=ticket.user_id,
        user_email=user.user_email if user else "Unknown",
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        is_pinned=ticket.is_pinned,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        message_count=len(messages),
        messages=[
            TicketMessageResponse(
                id=msg.id,
                ticket_id=msg.ticket_id,
                sender_id=msg.sender_id,
                sender_name=msg.sender.user_email if msg.sender else "Unknown",
                message_text=msg.message_text,
                created_at=msg.created_at
            ) for msg in messages
        ]
    )

@router.post("/api/tickets/{ticket_id}/messages", response_model=TicketMessageResponse)
async def add_message_to_ticket(
    ticket_id: int,
    message_data: TicketMessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Добавить сообщение в тикет"""
    # Проверяем права доступа
    await get_ticket_with_access_check(ticket_id, current_user)
    
    # Определяем, является ли отправитель техподдержкой
    is_staff = current_user.role_id in [RoleTypes.MODERATOR, RoleTypes.ADMIN, RoleTypes.SUPER_ADMIN]
    
    # ВСЕГДА отправляем как техподдержку для админов/модераторов
    # (или можно добавить логику на основе каких-то условий)
    send_as_tech_support = is_staff  # Всегда True для staff
    
    # Добавляем сообщение
    new_message = await TicketMessageDAO.add_message(
        ticket_id=ticket_id,
        sender_id=current_user.id,
        message_text=message_data.message_text,
        is_tech_support=send_as_tech_support
    )
    
    # Обновляем статус тикета
    if is_staff:
        new_status = TicketStatus.IN_PROGRESS
    else:
        new_status = TicketStatus.AWAITING_USER_RESPONSE
    
    await TicketDAO.update({"id": ticket_id}, status=new_status)
    
    # Получаем сообщение с информацией об отправителе
    async with async_session_maker() as session:
        message_query = (
            select(TicketMessage)
            .options(joinedload(TicketMessage.sender))
            .where(TicketMessage.id == new_message.id)
        )
        result = await session.execute(message_query)
        message_with_sender = result.unique().scalar_one()
    
    # Определяем отображаемое имя
    display_name = "Техподдержка" if send_as_tech_support else message_with_sender.sender.user_nick
    
    return TicketMessageResponse(
        id=message_with_sender.id,
        ticket_id=message_with_sender.ticket_id,
        sender_id=message_with_sender.sender_id,
        sender_name=display_name,
        sender_email=message_with_sender.sender.user_email if message_with_sender.sender else "Unknown",
        is_tech_support=send_as_tech_support,
        message_text=message_with_sender.message_text,
        created_at=message_with_sender.created_at
    )

# Частичные страницы для интеграции в ЛК
@router.get("/partials/user-tickets", response_class=HTMLResponse)
async def user_tickets_partial(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Частичная страница тикетов пользователя для ЛК"""
    return templates.TemplateResponse("partials/user_tickets.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/partials/admin-tickets", response_class=HTMLResponse)
async def admin_tickets_partial(
    request: Request,
    current_user: User = Depends(require_roles([RoleTypes.MODERATOR, RoleTypes.ADMIN, RoleTypes.SUPER_ADMIN]))
):
    """Частичная страница админских тикетов для ЛК"""
    return templates.TemplateResponse("partials/admin_tickets.html", {
        "request": request,
        "current_user": current_user
    })

# ======== Отладочные роуты ===========

# app/tickets/router.py - добавим отладочные endpoint'ы
@router.get("/api/debug/check-db")
async def debug_check_db():
    """Проверка подключения к БД и таблиц"""
    async with async_session_maker() as session:
        # Проверяем существование таблиц
        tables_check = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name IN ('tickets', 'ticket_messages', 'users')
        """))
        tables = [row[0] for row in tables_check]
        
        # Проверяем количество записей
        tickets_count = await session.scalar(select(func.count(Ticket.id)))
        messages_count = await session.scalar(select(func.count(TicketMessage.id)))
        
        return {
            "tables_found": tables,
            "tickets_count": tickets_count,
            "messages_count": messages_count
        }

@router.get("/api/debug/test-ticket")
async def debug_create_test_ticket(current_user: User = Depends(get_current_user)):
    """Создание тестового тикета для отладки"""
    try:
        test_ticket = TicketCreate(
            subject="Тестовый тикет",
            description="Это тестовый тикет созданный для отладки",
            priority="Medium"
        )
        
        return await create_ticket(test_ticket, current_user)
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/debug/admin-test")
async def debug_admin_test(current_user: User = Depends(require_roles([RoleTypes.MODERATOR, RoleTypes.ADMIN, RoleTypes.SUPER_ADMIN]))):
    """Тестовый endpoint для админских тикетов"""
    return {
        "tickets": [
            {
                "id": 1,
                "user_id": 123,
                "user_email": "test@example.com", 
                "subject": "Тестовый тикет",
                "description": "Описание тестового тикета",
                "status": "Open",
                "priority": "Medium", 
                "is_pinned": False,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "message_count": 1
            }
        ],
        "total_count": 1,
        "page": 1,
        "page_size": 25,
        "total_pages": 1
    }