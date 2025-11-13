# app/verificationcodes/dao.py
from sqlalchemy import delete
from datetime import datetime
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.verificationcodes.models import VerificationCode

class VerificationCodeDAO(BaseDAO):
    model = VerificationCode

    @classmethod
    async def cleanup_expired(cls):
        """Очистка просроченных кодов верификации"""
        async with async_session_maker() as session:
            try:
                # Удаляем коды, у которых истек срок действия
                stmt = delete(VerificationCode).where(
                    VerificationCode.expires_at < datetime.now()
                )
                result = await session.execute(stmt)
                await session.commit()
                
                deleted_count = result.rowcount
                return deleted_count
                
            except Exception as e:
                await session.rollback()
                raise e