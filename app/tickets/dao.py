# app/tickets/dao.py
from sqlalchemy import select, desc, func
from sqlalchemy.orm import joinedload, selectinload
from app.dao.base import BaseDAO
from app.tickets.models import Ticket, TicketMessage, TicketStatus, TicketPriority
from app.database import async_session_maker
from app.users.models import User  # Добавьте этот импорт
from typing import List, Optional

class TicketDAO(BaseDAO):
    model = Ticket

    @classmethod
    async def create_ticket_with_message(
        cls,
        user_id: int,
        subject: str,
        description: str,
        priority: str = "Medium"
    ):
        """Создать тикет с первым сообщением в одной транзакции"""
        async with async_session_maker() as session:
            try:
                # Создаем тикет
                ticket = Ticket(
                    user_id=user_id,
                    subject=subject,
                    description=description,
                    priority=priority,
                    status=TicketStatus.OPEN
                )
                session.add(ticket)
                await session.flush()  # Получаем ID без коммита
                
                # Создаем первое сообщение
                message = TicketMessage(
                    ticket_id=ticket.id,
                    sender_id=user_id,
                    message_text=description
                )
                session.add(message)
                
                await session.commit()
                await session.refresh(ticket)
                
                return ticket
                
            except Exception as e:
                await session.rollback()
                raise e

    @classmethod
    async def get_user_tickets(
        cls, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 25,
        status: Optional[str] = None
    ):
        """Получить тикеты пользователя"""
        async with async_session_maker() as session:
            query = select(Ticket).where(Ticket.user_id == user_id)

            if status:
                query = query.where(Ticket.status == status)

            # Подсчет
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await session.scalar(count_query) or 0

            # Данные с пагинацией
            query = query.order_by(desc(Ticket.updated_at))
            query = query.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(query)
            tickets = result.scalars().all()

            # Получаем пользователей и количество сообщений
            tickets_data = []
            for ticket in tickets:
                # Получаем пользователя
                user_query = select(User).where(User.id == ticket.user_id)
                user_result = await session.execute(user_query)
                user = user_result.scalar_one_or_none()

                # Получаем количество сообщений
                msg_count_query = select(func.count(TicketMessage.id)).where(TicketMessage.ticket_id == ticket.id)
                msg_count = await session.scalar(msg_count_query) or 0

                tickets_data.append({
                    'id': ticket.id,
                    'user_id': ticket.user_id,
                    'user_email': user.user_email if user else "Unknown",
                    'user_nick': getattr(user, 'user_nick', user.user_email if user else "User"),  # Добавляем user_nick
                    'subject': ticket.subject,
                    'description': ticket.description,
                    'status': ticket.status,
                    'priority': ticket.priority,
                    'is_pinned': ticket.is_pinned,
                    'created_at': ticket.created_at,
                    'updated_at': ticket.updated_at,
                    'message_count': msg_count
                })

            return {
                "tickets": tickets_data,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1
            }

    @classmethod
    async def get_admin_tickets(
        cls,
        page: int = 1,
        page_size: int = 25,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        user_id: Optional[int] = None,
        is_pinned: Optional[bool] = None
    ):
        """Получить все тикеты для админов с ограничением 300"""
        async with async_session_maker() as session:
            query = select(Ticket)

            if status:
                query = query.where(Ticket.status == status)
            if priority:
                query = query.where(Ticket.priority == priority)
            if user_id:
                query = query.where(Ticket.user_id == user_id)
            if is_pinned is not None:
                query = query.where(Ticket.is_pinned == is_pinned)

            # Подсчет общего количества (без пагинации для фильтров)
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await session.scalar(count_query) or 0

            # Ограничиваем общее количество 300
            effective_total_count = min(total_count, 300)

            # Данные с пагинацией
            query = query.order_by(desc(Ticket.is_pinned), desc(Ticket.updated_at))
            query = query.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(query)
            tickets = result.scalars().all()

            # Получаем пользователей и количество сообщений
            tickets_data = []
            for ticket in tickets:
                # Получаем пользователя
                user_query = select(User).where(User.id == ticket.user_id)
                user_result = await session.execute(user_query)
                user = user_result.scalar_one_or_none()

                # Получаем количество сообщений
                msg_count_query = select(func.count(TicketMessage.id)).where(TicketMessage.ticket_id == ticket.id)
                msg_count = await session.scalar(msg_count_query) or 0

                tickets_data.append({
                    'id': ticket.id,
                    'user_id': ticket.user_id,
                    'user_email': user.user_email if user else "Unknown",
                    'user_nick': getattr(user, 'user_nick', user.user_email if user else "User"),  # Добавляем user_nick
                    'subject': ticket.subject,
                    'description': ticket.description,
                    'status': ticket.status,
                    'priority': ticket.priority,
                    'is_pinned': ticket.is_pinned,
                    'created_at': ticket.created_at,
                    'updated_at': ticket.updated_at,
                    'message_count': msg_count
                })

            return {
                "tickets": tickets_data,
                "total_count": effective_total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (effective_total_count + page_size - 1) // page_size if page_size > 0 else 1
            }

    @classmethod
    async def get_first_ticket_message(cls, ticket_id: int):
        """Получить первое сообщение тикета (описание проблемы)"""
        async with async_session_maker() as session:
            query = (
                select(TicketMessage)
                .where(TicketMessage.ticket_id == ticket_id)
                .order_by(TicketMessage.created_at)
                .limit(1)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        
    @classmethod
    async def get_ticket_detail(cls, ticket_id: int, user_id: Optional[int] = None):
        """Получить детальную информацию о тикете"""
        async with async_session_maker() as session:
            # Получаем тикет
            ticket_query = select(Ticket).where(Ticket.id == ticket_id)
            if user_id:
                ticket_query = ticket_query.where(Ticket.user_id == user_id)

            ticket_result = await session.execute(ticket_query)
            ticket = ticket_result.scalar_one_or_none()

            if not ticket:
                return None

            # Получаем пользователя
            user_query = select(User).where(User.id == ticket.user_id)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()

            # Получаем сообщения с информацией об отправителях
            messages_query = (
                select(TicketMessage)
                .options(joinedload(TicketMessage.sender))
                .where(TicketMessage.ticket_id == ticket_id)
                .order_by(TicketMessage.created_at)
            )
            messages_result = await session.execute(messages_query)
            messages = messages_result.unique().scalars().all()

            # Получаем первое сообщение (описание проблемы)
            first_message = messages[0] if messages else None

            return {
                'ticket': ticket,
                'user': user,
                'messages': messages,
                'first_message': first_message
            }

    @classmethod
    async def get_ticket_stats(cls, user_id: Optional[int] = None):
        """Получить статистику по тикетам"""
        async with async_session_maker() as session:
            query = select(Ticket)
            
            if user_id:
                query = query.where(Ticket.user_id == user_id)
            
            result = await session.execute(query)
            tickets = result.scalars().all()
            
            # Считаем статистику
            stats = {
                "total": len(tickets),
                "by_status": {},
                "by_priority": {}
            }
            
            for ticket in tickets:
                # Статистика по статусам
                stats["by_status"][ticket.status] = stats["by_status"].get(ticket.status, 0) + 1
                # Статистика по приоритетам
                stats["by_priority"][ticket.priority] = stats["by_priority"].get(ticket.priority, 0) + 1
            
            return stats

    @classmethod
    async def can_access_ticket(cls, ticket_id: int, user: 'User') -> bool:
        """Проверяет права доступа пользователя к тикету"""
        from app.roles.models import RoleTypes
        from app.tickets.models import Ticket
        
        # Админы/модераторы имеют доступ ко всем тикетам
        if user.role_id in [RoleTypes.MODERATOR, RoleTypes.ADMIN, RoleTypes.SUPER_ADMIN]:
            return True
        
        # Обычные пользователи - только к своим тикетам
        ticket: Ticket | None = await cls.find_one_or_none_by_id(ticket_id)
        return ticket is not None and ticket.user_id == user.id
    
    @classmethod
    async def get_ticket(cls, ticket_id: int) -> Ticket | None:
        """Получить тикет по ID"""
        from app.tickets.models import Ticket
        result: Ticket | None = await cls.find_one_or_none_by_id(ticket_id)
        return result

    @classmethod
    async def auto_close_resolved(cls):
        """Автоматическое закрытие решенных тикетов"""
        async with async_session_maker() as session:
            try:
                # Находим тикеты, которые были решены более 7 дней назад
                from datetime import datetime, timedelta
                from sqlalchemy import update
                
                cutoff_date = datetime.now() - timedelta(days=7)
                
                stmt = update(Ticket).where(
                    Ticket.status == TicketStatus.IN_PROGRESS,
                    Ticket.updated_at < cutoff_date
                ).values(status=TicketStatus.CLOSED)
                
                result = await session.execute(stmt)
                await session.commit()
                
                closed_count = result.rowcount
                return closed_count
                
            except Exception as e:
                await session.rollback()
                raise e

    @classmethod
    async def get_ticket_with_user(cls, ticket_id: int):
        """Получить тикет с информацией о пользователе"""
        async with async_session_maker() as session:
            query = (
                select(Ticket)
                .options(joinedload(Ticket.user))
                .where(Ticket.id == ticket_id)
            )
            result = await session.execute(query)
            return result.unique().scalar_one_or_none()

class TicketMessageDAO(BaseDAO):
    model = TicketMessage

    @classmethod
    async def add_message(cls, ticket_id: int, sender_id: int, message_text: str, is_tech_support: bool = False):
        """Добавить сообщение"""
        async with async_session_maker() as session:
            message = TicketMessage(
                ticket_id=ticket_id,
                sender_id=sender_id,
                message_text=message_text,
                is_tech_support=is_tech_support  # Добавляем флаг техподдержки
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message