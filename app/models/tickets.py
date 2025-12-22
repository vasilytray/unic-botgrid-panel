# app/tickets/models.py
from sqlalchemy import Integer, Text, text, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional
from app.database import Base
from datetime import datetime

class TicketStatus:
    OPEN = "Open"
    IN_PROGRESS = "In Progress" 
    AWAITING_USER_RESPONSE = "Awaiting User Response"
    CLOSED = "Closed"

class TicketPriority:
    LOW = "Low"
    MEDIUM = "Medium" 
    HIGH = "High"
    URGENT = "Urgent"

class Ticket(Base):
    __tablename__ = 'tickets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=TicketStatus.OPEN, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default=TicketPriority.MEDIUM, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tickets", foreign_keys=[user_id])
    messages = relationship("TicketMessage", back_populates="tickets", cascade="all, delete-orphan")

class TicketMessage(Base):
    __tablename__ = 'ticket_messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("tickets.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_tech_support: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)  # Новый столбец
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tickets = relationship("Ticket", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])