# app/billing/dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import List, Optional

from app.database import async_session_maker
from app.billing.models import Invoice, Transaction

class InvoicesDAO:
    model = Invoice

    @classmethod
    async def get_pending_invoices_count(cls, user_id: int) -> int:
        """Получить количество неоплаченных счетов"""
        async with async_session_maker() as session:
            query = (select(func.count(cls.model.id))
                    .filter_by(user_id=user_id, status="pending"))
            result = await session.execute(query)
            return result.scalar()

    @classmethod
    async def get_user_invoices_count(cls, user_id: int) -> int:
        """Получить общее количество счетов пользователя"""
        async with async_session_maker() as session:
            query = (select(func.count(cls.model.id))
                    .filter_by(user_id=user_id))
            result = await session.execute(query)
            return result.scalar()

    @classmethod
    async def get_user_invoices(cls, user_id: int, limit: int = 50) -> List[Invoice]:
        """Получить счета пользователя"""
        async with async_session_maker() as session:
            query = (select(cls.model)
                    .options(joinedload(cls.model.user))
                    .filter_by(user_id=user_id)
                    .order_by(cls.model.created_at.desc())
                    .limit(limit))
            result = await session.execute(query)
            return result.unique().scalars().all()

class TransactionsDAO:
    model = Transaction

    @classmethod
    async def get_user_transactions(cls, user_id: int, limit: int = 50) -> List[Transaction]:
        """Получить транзакции пользователя"""
        async with async_session_maker() as session:
            query = (select(cls.model)
                    .options(
                        joinedload(cls.model.user),
                        joinedload(cls.model.invoice)
                    )
                    .filter_by(user_id=user_id)
                    .order_by(cls.model.created_at.desc())
                    .limit(limit))
            result = await session.execute(query)
            return result.unique().scalars().all()