# app/models/users.py
from sqlalchemy import Integer, ForeignKey, Text, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from datetime import datetime, timezone

from app.core.database import Base, int_pk, created_at, updated_at, str_uniq, str_null_true

class UserLog(Base):
    __tablename__ = "users_logs" # pyright: ignore[reportAssignmentType]
    
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[created_at]
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="logs")
    changer: Mapped["User"] = relationship("User", foreign_keys=[changed_by], back_populates="changes_made")

    def __str__(self):
        return f"UserLog(id={self.id}, user_id={self.user_id}, action={self.action_type})"

class UserAllowedIP(Base):
    __tablename__ = "users_allowed_ips" # type: ignore
    
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ip_address: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_active: Mapped[int] = mapped_column(default=1, server_default=text('1'))
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="allowed_ips")

    def __str__(self):
        return f"UserAllowedIP(id={self.id}, user_id={self.user_id}, ip={self.ip_address})"

class User(Base):
    __tablename__ = "users" # type: ignore
    
    id: Mapped[int_pk]
    user_phone: Mapped[str_uniq]
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    user_nick: Mapped[str_uniq] = mapped_column(nullable=True)
    user_pass: Mapped[str]
    user_email: Mapped[str_uniq]
    two_fa_auth: Mapped[int] = mapped_column(default=0, server_default=text('0'))
    email_verified: Mapped[int] = mapped_column(default=0, server_default=text('0'))
    phone_verified: Mapped[int] = mapped_column(default=0, server_default=text('0'))
    user_status: Mapped[Optional[int]] = mapped_column(nullable=True)
    special_notes: Mapped[str_null_true]
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), default=4)
    tg_chat_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    
    # Security fields
    last_login: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    secondary_email: Mapped[Optional[str]] = mapped_column(nullable=True)
    security_settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined") # type: ignore
    allowed_ips: Mapped[List["UserAllowedIP"]] = relationship(
        "UserAllowedIP", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    logs: Mapped[List["UserLog"]] = relationship(
        "UserLog", 
        foreign_keys=[UserLog.user_id], 
        back_populates="user"
    )
    changes_made: Mapped[List["UserLog"]] = relationship(
        "UserLog", 
        foreign_keys=[UserLog.changed_by], 
        back_populates="changer"
    )
    
    # Services relationships (будет добавлено позже)
    # services: Mapped[Optional[List["Service"]]] = relationship("Service", back_populates="user")
    # tickets = relationship("Ticket", back_populates="user", foreign_keys=[Ticket.user_id])
    # ticket_messages = relationship("TicketMessage", back_populates="sender", foreign_keys=[TicketMessage.sender_id])

    @property
    def is_admin(self) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return self.role_id in [1, 2]  # 1=SuperAdmin, 2=Admin
    
    @property
    def is_super_admin(self) -> bool:
        """Проверяет, является ли пользователь суперадмином"""
        return self.role_id == 1
    
    @property
    def is_moderator(self) -> bool:
        """Проверяет, является ли пользователь модератором"""
        return self.role_id in [1, 2, 3]  # 1=SuperAdmin, 2=Admin, 3=Moderator

    def to_dict(self):
        return {
            "id": self.id,
            "user_phone": self.user_phone,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "user_nick": self.user_nick,
            "user_email": self.user_email,
            "two_fa_auth": self.two_fa_auth,
            "email_verified": self.email_verified,
            "phone_verified": self.phone_verified,
            "user_status": self.user_status,
            "special_notes": self.special_notes,
            "role_id": self.role_id,
            "tg_chat_id": self.tg_chat_id,
            "last_login": self.last_login,
            "secondary_email": self.secondary_email,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def __str__(self):
        return f"User(id={self.id}, name={self.first_name} {self.last_name}, email={self.user_email})"