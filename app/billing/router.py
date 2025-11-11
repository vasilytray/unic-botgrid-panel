# app/billing/router.py
from fastapi import APIRouter, Depends
from app.users.dependencies import get_current_user
from app.database import async_session_maker
from app.users.models import User

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/balance")
async def get_balance(current_user: User = Depends(get_current_user)):
    """Получить баланс пользователя"""
    pass

@router.get("/invoices")
async def get_invoices(current_user: User = Depends(get_current_user)):
    """Получить историю счетов"""
    pass

@router.post("/deposit")
async def deposit_funds(
    amount: float,
    current_user: User = Depends(get_current_user)
):
    """Пополнить баланс"""
    pass