# # app/partials/router.py
# from fastapi import APIRouter, Request, Depends
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates

# from app.users.models import User
# from app.users.dependencies import get_current_user

# router = APIRouter(prefix="/partials", tags=["Partial Pages"])
# templates = Jinja2Templates(directory="app/templates")

# @router.get("/profile", response_class=HTMLResponse)
# async def get_profile_partial(
#     request: Request,
#     current_user: User = Depends(get_current_user)
# ):
#     """Возвращает частичную страницу профиля без layout"""
#     return templates.TemplateResponse("partials/profile.html", {
#         "request": request,
#         "current_user": current_user
#     })



# app/partials/router.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.users.models import User
from app.users.dependencies import get_current_user
from app.roles.dependencies import require_roles
from app.roles.models import Role, RoleTypes

router = APIRouter(prefix="/partials", tags=["Partial Pages"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/test")
async def test_partial():
    """Тестовый эндпоинт для проверки работы partials"""
    return JSONResponse({"status": "ok", "message": "Partials router is working"})

@router.get("/profile", response_class=HTMLResponse)
async def get_profile_partial(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Возвращает частичную страницу профиля без layout"""
    print(f"🔄 Загрузка частичного профиля для пользователя: {current_user.id}")
    
    try:
        response = templates.TemplateResponse("partials/profile.html", {
            "request": request,
            "current_user": current_user,
            # Передаем дату регистрации в ISO формате
            "registration_date": current_user.created_at.isoformat() if current_user.created_at else None,
            # "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            # Или в формате timestamp
            "registration_timestamp": int(current_user.created_at.timestamp()) if current_user.created_at else None,
            # "last_login_timestamp": int(current_user.last_login.timestamp()) if current_user.last_login else None
        })
        print("✅ Частичный профиль успешно сгенерирован")
        return response
    except Exception as e:
        print(f"❌ Ошибка при генерации частичного профиля: {e}")
        return HTMLResponse(f"<div class='error'>Ошибка загрузки профиля: {str(e)}</div>")

@router.get("/profile-simple", response_class=HTMLResponse)
async def get_profile_simple(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Упрощенная тестовая версия профиля"""
    return templates.TemplateResponse("partials/profile_simple.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/services/all", response_class=HTMLResponse)
async def get_all_services_partial(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Частичная страница всех сервисов"""
    try:
        from app.services.dao import ServicesDAO
        user_services = await ServicesDAO.get_user_services(current_user.id)
    except Exception as e:
        print(f"Ошибка загрузки сервисов: {e}")
        user_services = []
    
    return templates.TemplateResponse("partials/all_services.html", {
        "request": request,
        "current_user": current_user,
        "services": user_services
    })

@router.get("/services/vps", response_class=HTMLResponse)
async def get_vps_services_partial(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Частичная страница VPS сервисов"""
    return templates.TemplateResponse("partials/vps_services.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/services/docker", response_class=HTMLResponse)
async def get_docker_services_partial(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Частичная страница Docker сервисов"""
    return templates.TemplateResponse("partials/docker_services.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/services/n8n", response_class=HTMLResponse)
async def get_n8n_services_partial(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Частичная страница n8n сервисов"""
    return templates.TemplateResponse("partials/n8n_services.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/invoices", response_class=HTMLResponse)
async def get_invoices_partial(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Частичная страница счетов"""
    try:
        from app.billing.dao import InvoicesDAO
        user_invoices = await InvoicesDAO.get_user_invoices(current_user.id)
    except Exception as e:
        print(f"Ошибка загрузки счетов: {e}")
        user_invoices = []
    
    return templates.TemplateResponse("partials/invoices.html", {
        "request": request,
        "current_user": current_user,
        "invoices": user_invoices
    })

@router.get("/billing/history", response_class=HTMLResponse)
async def get_billing_history_partial(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Частичная страница истории операций"""
    return templates.TemplateResponse("partials/billing_history.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/projects", response_class=HTMLResponse)
async def get_projects_partial(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Частичная страница проектов"""
    return templates.TemplateResponse("partials/projects.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/tutorial/{tutorial_name}", response_class=HTMLResponse)
async def get_tutorial_partial(
    request: Request,
    tutorial_name: str,
    current_user: User = Depends(get_current_user)
):
    """Возвращает частичные страницы туториалов"""
    template_map = {
        "vps-setup": "partials/tutorials/vps_setup.html",
        "docker-basics": "partials/tutorials/docker_basics.html",
        "n8n-intro": "partials/tutorials/n8n_intro.html",
    }
    
    template_name = template_map.get(tutorial_name, "partials/tutorials/default.html")
    
    return templates.TemplateResponse(template_name, {
        "request": request,
        "current_user": current_user,
        "tutorial_name": tutorial_name
    })

@router.get("/edit-basic-profile", response_class=HTMLResponse)
async def get_edit_basic_profile(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Страница редактирования основных данных"""
    return templates.TemplateResponse(
        "partials/edit_basic_profile.html",
        {"request": request, "current_user": current_user}
    )

@router.get("/edit-password", response_class=HTMLResponse)
async def get_edit_password(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Страница смены пароля"""
    return templates.TemplateResponse(
        "partials/edit_password.html", 
        {"request": request, "current_user": current_user}
    )

@router.get("/edit-security", response_class=HTMLResponse)
async def get_edit_security(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Страница управления безопасностью"""
    return templates.TemplateResponse(
        "partials/edit_security.html",
        {"request": request, "current_user": current_user}
    )

@router.get("/tickets/user")
async def user_tickets_partial(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Частичная страница тикетов пользователя"""
    return templates.TemplateResponse("partials/user_tickets.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/tickets/admin")
async def admin_tickets_partial(
    request: Request,
    current_user: User = Depends(require_roles([RoleTypes.MODERATOR, RoleTypes.ADMIN, RoleTypes.SUPER_ADMIN]))
):
    """Частичная страница админских тикетов"""
    return templates.TemplateResponse("partials/admin_tickets.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/tickets/admin_ticket_request")
async def admin_ticket_request_partial(
    request: Request,
    current_user: User = Depends(require_roles([RoleTypes.MODERATOR, RoleTypes.ADMIN, RoleTypes.SUPER_ADMIN]))
):
    """Частичная страница управления тикетом для админов"""
    return templates.TemplateResponse("partials/admin_ticket_request.html", {
        "request": request,
        "current_user": current_user
    })