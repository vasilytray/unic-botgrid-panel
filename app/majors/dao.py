from app.dao.base import BaseDAO
from sqlalchemy.future import select
from app.database import async_session_maker
from app.majors.models import  Major

class MajorsDAO(BaseDAO):
    model = Major

    @classmethod
    async def find_full_data(cls, major_id: int):
        async with async_session_maker() as session:
            # Запрос для получения информации о пользователе вместе с информацией о группе
            query_major = select(Major).filter_by(id=major_id)
            result_major = await session.execute(query_major)
            major_info = result_major.scalars().all()

            major_data = major_info.to_dict()
            major_data['major'] = major_info.major.major_name
            return major_data