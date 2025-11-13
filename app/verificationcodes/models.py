# app/verificationcodes/models.py
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.users.models import User
from datetime import datetime

class VerificationCode(Base):
        
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    code: Mapped[str]
    type: Mapped[str]  # 'email' или 'phone'
    expires_at: Mapped[datetime]
    
    user: Mapped["User"] = relationship("User", back_populates="verification_codes")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"
