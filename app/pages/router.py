# app/pages/router.py
from fastapi import APIRouter, Request, Depends, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import shutil

from app.users.models import User
from app.users.dependencies import get_current_user, get_current_admin, get_current_moderator, get_current_super_admin, get_optional_user, validate_role_change, log_role_change

from app.students.router import get_all_students, get_student_by_id
from app.users.router import get_me

# router = APIRouter(prefix='/pages', tags=['Фронтенд'])
router = APIRouter(prefix='', tags=['Фронтенд'])
templates = Jinja2Templates(directory='app/templates')

@router.get('/', response_class=HTMLResponse)
async def home_page(request: Request, current_user: User = Depends(get_optional_user)):
    """Главная страница"""
    return templates.TemplateResponse("main.html", {
        "request": request,
        "user": current_user
    })

@router.get('/auth', response_class=HTMLResponse)
async def auth_page(request: Request, current_user: User = Depends(get_optional_user)):
    """Страница авторизации/регистрации"""
    return templates.TemplateResponse("auth.html", {
        "request": request,
        "user": current_user
    })

# @router.get('/lk/plist', response_class=HTMLResponse)
# async def services_dashboard(
#     request: Request,
#     current_user: User = Depends(get_current_user)
# ):
#     """Панель управления пользователя с статистикой сервисов"""
    
#     try:
#         from app.services.dao import ServicesDAO
#         from app.billing.dao import InvoicesDAO
        
#         # Получаем реальные данные
#         user_services = await ServicesDAO.get_user_services(current_user.id)
#         pending_invoices_count = await InvoicesDAO.get_pending_invoices_count(current_user.id)
#         total_invoices_count = await InvoicesDAO.get_user_invoices_count(current_user.id)
#         service_stats = await ServicesDAO.get_user_service_stats(current_user.id)
        
#     except Exception as e:
#         print(f"Ошибка загрузки данных: {e}")
#         # Используем временные данные
#         user_services = []
#         pending_invoices_count = 0
#         total_invoices_count = 0
#         service_stats = {"by_type": {}, "by_status": {}}
    
#     return templates.TemplateResponse("servicesdb.html", {
#         "request": request,
#         "user": current_user,
#         "services": user_services,
#         "total_services": len(user_services),
#         "pending_invoices_count": pending_invoices_count,
#         "total_invoices_count": total_invoices_count,
#         "service_stats": service_stats
#     })

# @router.get('/lk/services', response_class=HTMLResponse)
# async def my_services(
#     request: Request,
#     current_user: User = Depends(get_current_user)
# ):
#     """Страница с детальным списком сервисов"""
#     user_services = []
    
#     try:
#         from app.services.dao import ServicesDAO
#         user_services = await ServicesDAO.get_user_services(current_user.id)
#     except Exception as e:
#         print(f"Ошибка загрузки сервисов: {e}")
    
#     return templates.TemplateResponse("my_services.html", {
#         "request": request,
#         "user": current_user,
#         "services": user_services
#     })

# @router.get('/lk/invoices', response_class=HTMLResponse)
# async def my_invoices(
#     request: Request,
#     current_user: User = Depends(get_current_user)
# ):
#     """Страница с счетами"""
#     user_invoices = []
    
#     try:
#         from app.billing.dao import InvoicesDAO
#         user_invoices = await InvoicesDAO.get_user_invoices(current_user.id)
#     except Exception as e:
#         print(f"Ошибка загрузки счетов: {e}")
    
#     return templates.TemplateResponse("my_invoices.html", {
#         "request": request,
#         "user": current_user,
#         "invoices": user_invoices
#     })


@router.get('/students')
async def get_students_html(request: Request, student=Depends(get_all_students)):
    return templates.TemplateResponse(name='students.html',
                                      context={'request': request, 'students': student})
@router.get('/students/{student_id}')
async def get_students_html(request: Request, student=Depends(get_student_by_id)):
    return templates.TemplateResponse(name='student.html',
                                      context={'request': request, 'student': student})

@router.get('/profile')
async def get_my_profile(request: Request, profile=Depends(get_me)):
    return templates.TemplateResponse(name='profile.html', context={'request': request, 'profile': profile})


@router.get('/register')
async def get_students_html(request: Request):
    return templates.TemplateResponse(name='register_form.html', context={'request': request})


@router.get('/login')
async def get_students_html(request: Request):
    return templates.TemplateResponse(name='login_form.html', context={'request': request})

@router.post('/add_photo')
async def add_student_photo(file: UploadFile, image_name: int):
    with open(f"app/static/images/{image_name}.webp", "wb+") as photo_obj:
        shutil.copyfileobj(file.file, photo_obj)

# временный эндпоинт для диагностики
@router.get('/debug/partials')
async def debug_partials(request: Request, current_user: User = Depends(get_current_user)):
    """Страница для тестирования partials"""
    return templates.TemplateResponse("debug_partials.html", {
        "request": request,
        "current_user": current_user
    })