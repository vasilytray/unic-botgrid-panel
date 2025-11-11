# app/lk/router.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.users.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix='/lk', tags=['Личный кабинет'])
templates = Jinja2Templates(directory='app/templates')

@router.get("/plist", response_class=HTMLResponse)
async def services_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Панель управления пользователя с статистикой сервисов"""
    print(f"📊 Загрузка панели управления для пользователя: {current_user.id}")
    
    try:
        from app.services.dao import ServicesDAO
        from app.billing.dao import InvoicesDAO
        
        # Получаем реальные данные
        user_services = await ServicesDAO.get_user_services(current_user.id)
        pending_invoices_count = await InvoicesDAO.get_pending_invoices_count(current_user.id)
        total_invoices_count = await InvoicesDAO.get_user_invoices_count(current_user.id)
        service_stats = await ServicesDAO.get_user_service_stats(current_user.id)
        
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        # Используем временные данные
        user_services = []
        pending_invoices_count = 0
        total_invoices_count = 0
        service_stats = {"by_type": {}, "by_status": {}}
    
    # return templates.TemplateResponse("servicesdb.html", {
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "user_authenticated": True,
        "services": user_services,
        "total_services": len(user_services),
        "pending_invoices_count": pending_invoices_count,
        "total_invoices_count": total_invoices_count,
        "service_stats": service_stats,
        "active_tab": "dashboard"  # Для подсветки активного пункта меню
    })

@router.get("/services", response_class=HTMLResponse)
async def my_services(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Страница с детальным списком сервисов"""
    user_services = []
    
    try:
        from app.services.dao import ServicesDAO
        user_services = await ServicesDAO.get_user_services(current_user.id)
    except Exception as e:
        print(f"Ошибка загрузки сервисов: {e}")
    
    return templates.TemplateResponse("my_services.html", {
        "request": request,
        "user": current_user,
        "services": user_services
    })

@router.get("/invoices", response_class=HTMLResponse)
async def my_invoices(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Страница с счетами"""
    user_invoices = []
    
    try:
        from app.billing.dao import InvoicesDAO
        user_invoices = await InvoicesDAO.get_user_invoices(current_user.id)
    except Exception as e:
        print(f"Ошибка загрузки счетов: {e}")
    
    return templates.TemplateResponse("my_invoices.html", {
        "request": request,
        "user": current_user,
        "invoices": user_invoices
    })