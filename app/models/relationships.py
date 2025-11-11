# app/models/relationships.py
"""
Настройка отношений между моделями после их регистрации
"""
from sqlalchemy.orm import relationship

def configure_relationships():
    """Настраивает все отношения между моделями"""
    from app.users.models import User
    from app.services.models import Service
    from app.billing.models import Invoice, Transaction
    
    # Настраиваем отношения для User
    User.services = relationship(
        "Service", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    User.invoices = relationship(
        "Invoice", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    User.transactions = relationship(
        "Transaction", 
        back_populates="user", 
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    # Настраиваем отношения для Service
    Service.user = relationship(
        "User", 
        back_populates="services",
        lazy="joined"
    )
    
    # Настраиваем отношения для Invoice
    Invoice.user = relationship(
        "User", 
        back_populates="invoices",
        lazy="joined"
    )
    Invoice.transactions = relationship(
        "Transaction", 
        back_populates="invoice",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    # Настраиваем отношения для Transaction
    Transaction.user = relationship(
        "User", 
        back_populates="transactions",
        lazy="joined"
    )
    Transaction.invoice = relationship(
        "Invoice", 
        back_populates="transactions",
        lazy="joined"
    )
    
    print("✅ Все отношения между моделями настроены")