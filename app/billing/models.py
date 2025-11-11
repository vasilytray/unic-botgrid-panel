# app/billing/models.py
from sqlalchemy import String, Float, Integer, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from typing import Optional, List
from datetime import datetime

from app.users.models import User
from app.database import Base, int_pk, created_at, updated_at, datetime_null_true

class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Invoice(Base):
    __tablename__ = "invoices"
    
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[float] = mapped_column(nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(SQLEnum(InvoiceStatus), default=InvoiceStatus.PENDING)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime_null_true]
    paid_at: Mapped[datetime_null_true]
    
    # Связи
    # user: Mapped["User"] = relationship(back_populates="invoices")
    # transactions: Mapped[List["Transaction"]] = relationship(back_populates="invoice")
    
    def __str__(self):
        return f"Invoice(id={self.id}, amount={self.amount}, status={self.status})"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    invoice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("invoices.id"), nullable=True)
    amount: Mapped[float] = mapped_column(nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20))  # deposit, payment, refund
    status: Mapped[str] = mapped_column(String(20), default="completed")  # pending, completed, failed
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Связи
    # user: Mapped["User"] = relationship(back_populates="transactions")
    # invoice: Mapped[Optional["Invoice"]] = relationship(back_populates="transactions")
    
    created_at: Mapped[created_at]

    def __str__(self):
        return f"Transaction(id={self.id}, type={self.transaction_type}, amount={self.amount})"