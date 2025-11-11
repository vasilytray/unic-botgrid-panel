from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import Optional, List
import re
import random
import json
import logging
import asyncio
from jose import jwt, JWTError
from app.config import get_auth_data
from app.tasks.log_cleanup_task import log_cleanup
from app.logger import app_logger as logger
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.users.auth import get_password_hash, authenticate_user, create_access_token
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException, PasswordMismatchException
from app.users.dao import UsersDAO, UserLogsDAO
from app.roles.dao import RolesDAO
from app.users.rb import RBUser
from app.users.models import User
from app.utils.secutils import SecurityUtils
from app.users.log_cleaner import LogCleaner
from app.tasks.background_tasks import background_tasks
from app.users.ip_dao import UserAllowedIPsDAO
from app.users.schemas import SUserBase, SUserAdd, SUserResponse, SUserListResponse, SUserAuth
from app.users.schemas import SUserRegister, SUserByEmailResponse, SUserUpdateProfile, SUserChangePassword
from app.users.schemas import SUserUpdateRole, SUserUpdateRoleResponse, SUserUpdateRoleByEmail, SUserRoleInfo
from app.users.schemas import SUserLogResponse, SUserLogsList, SRoleChangeLog, SUserRead, SUserAddSecondaryEmail
from app.users.schemas import SUserIPRestriction, SUserProfileResponse, SUserAddIP, SUserRemoveIP, SUserAllowedIPResponse
from app.users.schemas import SUserAllowedIPBase
from app.users.dependencies import get_current_user, get_current_admin, get_current_moderator, get_current_super_admin, validate_role_change, log_role_change

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory='app/templates')

# router = APIRouter(prefix='/auth', tags=['Auth'])

router = APIRouter(prefix='/users', tags=['Работа с пользователями'])
# Настройка логирования
# logger = logging.getLogger(__name__)

def log_info(message: str):
    logger.info(message)

def log_error(message: str):
    logger.error(message)

def log_success(message: str):
    logger.info(f"✅ {message}")

# @router.get("/list_users", response_model=List[SUserRead])
# async def get_users():
#     users_all = await UsersDAO.find_all()
#     # Используем генераторное выражение для создания списка
#     return [{'id': user.id, 'name': user.name} for user in users_all]

@router.get("/", response_class=HTMLResponse, summary="Страница авторизации")
async def get_categories(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})

@router.post("/register/")
async def register_user(user_data: SUserRegister) -> dict:
    from app.users.dao import UsersDAO
    
    # Проверяем существование пользователя по email
    user_by_email = await UsersDAO.find_by_email(user_data.user_email)
    if user_by_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким email уже существует'
        )
    
    # Проверяем существование пользователя по телефону
    user_by_phone = await UsersDAO.find_by_phone(user_data.user_phone)
    if user_by_phone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким телефоном уже существует'
        )

    # Генерируем уникальный ник, если не указан
    user_dict = user_data.model_dump(exclude={'user_pass_check'})
    
    if not user_dict.get('user_nick'):
        user_dict['user_nick'] = await generate_unique_nick(
            user_data.first_name, 
            user_data.last_name
        )

    user_dict['user_pass'] = get_password_hash(user_data.user_pass)
    
    await UsersDAO.add_user(**user_dict)
    return {'message': f'Вы успешно зарегистрированы!'}


async def generate_unique_nick(first_name: str, last_name: str) -> str:
    """Генерирует уникальный никнейм"""
   
    
    base_nick = _create_base_nick(first_name, last_name)
    unique_nick = base_nick
    counter = 1
    
    # Проверяем уникальность ника и добавляем цифры при необходимости
    while counter <= 100:
        existing_user = await UsersDAO.find_one_or_none(user_nick=unique_nick)
        if not existing_user:
            break
        
        # Если ник уже существует, добавляем цифру
        if counter == 1:
            unique_nick = f"{base_nick}_{counter}"
        else:
            # Обрезаем base_nick если нужно место для цифр
            max_base_length = 47 - len(str(counter))
            truncated_base = base_nick[:max_base_length]
            unique_nick = f"{truncated_base}_{counter}"
        
        counter += 1
    
    # Если все варианты заняты, генерируем случайный
    if counter > 100:
        import random
        unique_nick = f"user_{random.randint(10000, 99999)}"
    
    return unique_nick


def _create_base_nick(first_name: str, last_name: str) -> str:
    """Создает базовый никнейм из имени и фамилии"""
    import re
    
    # Транслитерация кириллицы в латиницу
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
        'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '',
        'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    def transliterate(text: str) -> str:
        """Транслитерирует кириллический текст в латиницу"""
        result = []
        for char in text:
            if char in translit_map:
                result.append(translit_map[char])
            elif char.isalnum():
                result.append(char)
            else:
                result.append('_')
        return ''.join(result)
    
    # Транслитерируем имя и фамилию
    first_latin = transliterate(first_name.lower())
    last_latin = transliterate(last_name.lower())
    
    # Убираем лишние символы и создаем ник
    first_clean = re.sub(r'[^a-z0-9]', '', first_latin)
    last_clean = re.sub(r'[^a-z0-9]', '', last_latin)
    
    # Если после очистки что-то пустое, используем альтернативные варианты
    if not first_clean and not last_clean:
        return f"user_{hash(first_name + last_name) % 10000:04d}"
    elif not first_clean:
        return last_clean[:47] if len(last_clean) > 47 else last_clean
    elif not last_clean:
        return first_clean[:47] if len(first_clean) > 47 else first_clean
    
    # Создаем базовый ник
    base_nick = f"{first_clean}_{last_clean}"
    
    # Обрезаем если слишком длинный
    if len(base_nick) > 50:
        base_nick = base_nick[:50]
    
    return base_nick

# @router.post("/login/")
# async def auth_user(response: Response, user_data: SUserAuth):
#     check = await authenticate_user(user_email=user_data.user_email, user_pass=user_data.user_pass)
#     if check is None:
#         # raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#         #                     detail='Неверно указаны почта или пароль')
#          raise IncorrectEmailOrPasswordException
#     access_token = create_access_token({"sub": str(check.id)})
#     # response.set_cookie(key="users_access_token", value=access_token, httponly=True)
#     response.set_cookie(
#         key="users_access_token", 
#         value=access_token, 
#         httponly=True,
#         max_age=30*24*60*60,  # 30 дней
#         path="/"
#     )
#     # return {'ok': True, 'access_token': access_token, 'refresh_token': None, 'message': f'Авторизация успешна!'}
#     # Возвращаем JSON ответ вместо редиректа
#     # return {
#     #     "ok": True, 
#     #     "access_token": access_token, 
#     #     "refresh_token": None, 
#     #     "message": "Авторизация успешна!",
#     #     "redirect_url": "/lk/plist"  # Добавляем URL для редиректа на клиенте
#     # }
#     # Возвращаем JSONResponse с явным указанием Content-Type
#     return JSONResponse(
#         content={
#             "ok": True, 
#             "message": "Авторизация успешна!",
#             "redirect_url": "/lk/plist",
#             "user_id": check.id
#         },
#         status_code=200
#     )

@router.post("/login/")
async def auth_user(response: Response, user_data: SUserAuth, request: Request):
    check = await authenticate_user(
        user_email=user_data.user_email, 
        user_pass=user_data.user_pass,
        request=request  # Передаем request для проверки IP
    )
    if check is None:
        raise IncorrectEmailOrPasswordException
    
    # Обновляем время последнего входа
    success = await UsersDAO.update_last_login(check.id)
    if not success:
        log_error(f"Не удалось обновить last_login для пользователя {check.id}")
    
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(
        key="users_access_token", 
        value=access_token, 
        httponly=True,
        max_age=30*24*60*60,
        path="/"
    )
    
    # Логируем успешный вход с IP
    client_ip = SecurityUtils.get_client_ip(request)
    await UserLogsDAO.create_log(
        user_id=check.id,
        action_type='login',
        old_value=None,
        new_value=f"ip:{client_ip}",
        description=f'Успешный вход в систему с IP {client_ip}',
        changed_by=check.id
    )
    
    result = {
        "ok": True,
        "message": "Авторизация успешна!",
        "redirect_url": "/lk/plist",
        "user_id": check.id,
        "user_name": f"{check.first_name} {check.last_name}",
        "ip_address": client_ip
    }
    
    return result

@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)):
    return user_data

@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}

@router.get("/all/", summary="Получить список всех пользователей", response_model=SUserListResponse)
async def get_all_users(
    current_user: User = Depends(get_current_admin),
    request_body: RBUser = Depends()
    ) -> SUserListResponse:
    # Используем метод с загрузкой ролей
    users = await UsersDAO.find_all_with_roles(**request_body.to_dict())
    
    # Преобразуем пользователей в схему ответа
    user_responses = []
    for user in users:
        user_response = SUserResponse(
            id=user.id,
            user_phone=user.user_phone,
            first_name=user.first_name,
            last_name=user.last_name,
            user_nick=user.user_nick,
            user_email=user.user_email,
            user_status=user.user_status,
            role_id=user.role_id,
            special_notes=user.special_notes,
            role=user.role  # объект Role автоматически преобразуется в RoleResponse
        )
        user_responses.append(user_response)
    
    return SUserListResponse(users=user_responses, total=len(user_responses))

@router.get("/all_users/")
async def get_all_users(user_data: User = Depends(get_current_super_admin)):
    return await UsersDAO.find_all()

# @router.get("/all_users/")
# async def get_all_users(user_data: User = Depends(get_current_super_admin)):
#     return await UsersDAO.find_all()

@router.get("/{user_id}", summary="Получить одного пользователя по id", response_model=SUserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_moderator)
    ) -> SUserResponse:
    user_data = await UsersDAO.find_full_data(user_id)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Пользователь с ID {user_id} не найден!'
        )
    
    # return SUserResponse(**user_data)
    return SUserResponse.model_validate(user_data)

@router.get("/by-email/", 
           summary="Получить пользователя по email", 
           response_model=SUserByEmailResponse)
async def get_user_by_email(
    email: str,
    current_user: User = Depends(get_current_user)
) -> SUserByEmailResponse:
    """
    Получить информацию о пользователе по email.
    
    Правила доступа:
    - Админы и суперадмины: могут видеть любого пользователя
    - Обычные пользователи: могут видеть только свою информацию
    """
    # Проверяем права доступа
    if current_user.role_id not in [1, 2] and current_user.user_email != email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете просматривать только свою информацию"
        )
    
    user_data = await UsersDAO.find_by_email_with_role(email)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Пользователь с email {email} не найден!'
        )
    
    return SUserByEmailResponse.model_validate(user_data)


@router.post("/add/")
async def add_user(
    user: SUserAdd,
    current_user: User = Depends(get_current_admin)
    ) -> dict:
    """Добавить пользователя (только для админов)"""
    # Проверяем уникальность email и телефона
    # existing_user = await UsersDAO.find_one_or_none(user_email=user.user_email)
    existing_user = await UsersDAO.find_by_email(user.user_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким email уже существует'
        )
    
    # existing_user = await UsersDAO.find_one_or_none(user_phone=user.user_phone)
    existing_user = await UsersDAO.find_by_phone(user.user_phone)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким телефоном уже существует'
        )

    user_data = user.model_dump()
    user_data['user_pass'] = get_password_hash(user_data['user_pass'])
    
    user_id = await UsersDAO.add_user(**user_data)
    if user_id:
        return {"message": "Пользователь успешно добавлен!", "user_id": user_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при добавлении пользователя!"
        )
    
@router.put("/update-role/", 
           summary="Изменить роль пользователя по ID", 
           response_model=SUserUpdateRoleResponse)
async def update_user_role(
    role_data: SUserUpdateRole,
    super_admin: User = Depends(get_current_super_admin)
) -> SUserUpdateRoleResponse:
    """
    Изменить роль пользователя по ID (только для суперадминистратора).
    """
    # Валидация изменения роли
    target_user = await validate_role_change(super_admin, role_data.user_id, role_data.new_role_id)
    
    # Проверяем существование новой роли
    new_role = await RolesDAO.find_by_id(role_data.new_role_id)
    if not new_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Роль с ID {role_data.new_role_id} не найдена"
        )
    
    # Сохраняем старую роль
    old_role_id = target_user.role_id
    old_role_name = await RolesDAO.get_role_name_by_id(old_role_id)
    
    # Обновляем роль (используем обновленный метод с счетчиками)
    success = await UsersDAO.update_user_role(role_data.user_id, role_data.new_role_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении роли пользователя"
        )
    
    # Логируем изменение роли
    await log_role_change(
        user_id=role_data.user_id,
        old_role_id=old_role_id,
        new_role_id=role_data.new_role_id,
        changed_by=super_admin.id,
        description=f"Роль изменена суперадминистратором {super_admin.user_email}"
    )
    
    return SUserUpdateRoleResponse(
        message="Роль пользователя успешно обновлена",
        user_id=role_data.user_id,
        old_role_id=old_role_id,
        new_role_id=role_data.new_role_id,
        user_email=target_user.user_email,
        role_name=new_role.role_name
    )

@router.put("/update-role-by-email/", 
           summary="Изменить роль пользователя по email", 
           response_model=SUserUpdateRoleResponse)
async def update_user_role_by_email(
    role_data: SUserUpdateRoleByEmail,
    super_admin: User = Depends(get_current_super_admin)
) -> SUserUpdateRoleResponse:
    """
    Изменить роль пользователя по email (только для суперадминистратора).
    """
    # Находим пользователя по email
    target_user = await UsersDAO.find_by_email_with_role(role_data.user_email)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с email {role_data.user_email} не найден"
        )
    
    # Валидация изменения роли
    await validate_role_change(super_admin, target_user.id, role_data.new_role_id)
    
    # Проверяем существование новой роли
    new_role = await RolesDAO.find_by_id(role_data.new_role_id)
    if not new_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Роль с ID {role_data.new_role_id} не найдена"
        )
    
    # Сохраняем старую роль
    old_role_id = target_user.role_id
    old_role_name = await RolesDAO.get_role_name_by_id(old_role_id)
    
    # Обновляем роль
    success = await UsersDAO.update_user_role_by_email(role_data.user_email, role_data.new_role_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении роли пользователя"
        )
    
    # Логируем изменение роли
    await log_role_change(
        user_id=target_user.id,
        old_role_id=old_role_id,
        new_role_id=role_data.new_role_id,
        changed_by=super_admin.id,
        description=f"Роль изменена по email суперадминистратором {super_admin.user_email}"
    )
    
    return SUserUpdateRoleResponse(
        message="Роль пользователя успешно обновлена",
        user_id=target_user.id,
        old_role_id=old_role_id,
        new_role_id=role_data.new_role_id,
        user_email=target_user.user_email,
        role_name=new_role.role_name
    )

# Новые роутеры для работы с логами
@router.get("/logs/", 
           summary="Получить логи пользователей", 
           response_model=SUserLogsList)
async def get_users_logs(
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    admin_user: User = Depends(get_current_super_admin)
) -> SUserLogsList:
    """
    Получить логи пользователей (только для администраторов).
    """
    # Собираем фильтры
    filters = {}
    if user_id:
        filters['user_id'] = user_id
    if action_type:
        filters['action_type'] = action_type
    
    # Получаем логи с помощью BaseDAO
    logs = await UserLogsDAO.find_all(**filters)
    
    # Сортируем и ограничиваем результат (так как BaseDAO не поддерживает сортировку и пагинацию напрямую)
    sorted_logs = sorted(logs, key=lambda x: x.created_at, reverse=True)
    paginated_logs = sorted_logs[offset:offset + limit]
    
    # Преобразуем в схему ответа
    log_responses = []
    for log in paginated_logs:
        # Получаем связанные данные пользователей
        user = await UsersDAO.find_one_or_none_by_id(log.user_id) if log.user_id else None
        changer = await UsersDAO.find_one_or_none_by_id(log.changed_by) if log.changed_by else None
        
        log_response = SUserLogResponse(
            id=log.id,
            user_id=log.user_id,
            changed_by=log.changed_by,
            action_type=log.action_type,
            old_value=log.old_value,
            new_value=log.new_value,
            description=log.description,
            created_at=log.created_at,
            user_email=user.user_email if user else None,
            changer_email=changer.user_email if changer else None,
            user_name=f"{user.first_name} {user.last_name}" if user else None,
            changer_name=f"{changer.first_name} {changer.last_name}" if changer else None
        )
        log_responses.append(log_response)
    
    return SUserLogsList(logs=log_responses, total=len(sorted_logs))

@router.get("/logs/role-changes/", 
           summary="Получить логи изменений ролей", 
           response_model=list[SRoleChangeLog])
async def get_role_change_logs(
    user_id: Optional[int] = None,
    days: int = 30,
    admin_user: User = Depends(get_current_super_admin)
) -> list[SRoleChangeLog]:
    """
    Получить логи изменений ролей (только для администраторов).
    """
    logs = await UserLogsDAO.get_recent_role_changes(days=days)
    
    # Если нужна фильтрация по конкретному пользователю
    if user_id:
        logs = [log for log in logs if log.user_id == user_id]
    
    role_change_logs = []
    for log in logs:
        if log.action_type == 'role_change':
            # Парсим old_value и new_value
            old_role_info = log.old_value.split(':') if log.old_value else ['', '', '']
            new_role_info = log.new_value.split(':') if log.new_value else ['', '', '']
            
            role_change_log = SRoleChangeLog(
                id=log.id,
                user_id=log.user_id,
                user_email=log.user.user_email if log.user else "Unknown",
                user_name=f"{log.user.first_name} {log.user.last_name}" if log.user else "Unknown User",
                old_role=old_role_info[2] if len(old_role_info) > 2 else "Unknown",
                new_role=new_role_info[2] if len(new_role_info) > 2 else "Unknown",
                changed_by=f"{log.changer.first_name} {log.changer.last_name}" if log.changer else "Unknown",
                changer_email=log.changer.user_email if log.changer else "Unknown",
                created_at=log.created_at
            )
            role_change_logs.append(role_change_log)
    
    return role_change_logs

@router.get("/{user_id}/logs/", 
           summary="Получить логи конкретного пользователя", 
           response_model=SUserLogsList)
async def get_user_logs(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    admin_user: User = Depends(get_current_super_admin)
) -> SUserLogsList:
    """
    Получить логи конкретного пользователя (только для администраторов).
    """
    logs = await UserLogsDAO.get_user_logs(user_id, limit=limit, offset=offset)
    
    log_responses = []
    for log in logs:
        log_response = SUserLogResponse(
            id=log.id,
            user_id=log.user_id,
            changed_by=log.changed_by,
            action_type=log.action_type,
            old_value=log.old_value,
            new_value=log.new_value,
            description=log.description,
            created_at=log.created_at,
            user_email=log.user.user_email if log.user else None,
            changer_email=log.changer.user_email if log.changer else None,
            user_name=f"{log.user.first_name} {log.user.last_name}" if log.user else None,
            changer_name=f"{log.changer.first_name} {log.changer.last_name}" if log.changer else None
        )
        log_responses.append(log_response)
    
    return SUserLogsList(logs=log_responses, total=len(log_responses))

@router.get("/available-roles/", 
           summary="Получить список доступных ролей для назначения")
async def get_available_roles(
    super_admin: User = Depends(get_current_super_admin)
) -> list[dict]:
    """
    Получить список ролей, которые можно назначать пользователям.
    Исключает роль суперадминистратора.
    """
    roles = await RolesDAO.get_available_roles(exclude_super_admin=True)
    return [
        {
            "id": role.id,
            "name": role.role_name,
            "description": role.role_description,
            "user_count": role.count_users
        }
        for role in roles
    ]

@router.get("/{user_id}/role-info", 
           summary="Получить информацию о роли пользователя", 
           response_model=SUserRoleInfo)
async def get_user_role_info(
    user_id: int,
    super_admin: User = Depends(get_current_super_admin)
) -> SUserRoleInfo:
    """
    Получить подробную информацию о роли пользователя.
    """
    user = await UsersDAO.get_user_with_role_info(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    
    return SUserRoleInfo(
        id=user.id,
        user_email=user.user_email,
        first_name=user.first_name,
        last_name=user.last_name,
        current_role_id=user.role_id,
        current_role_name=user.role.role_name,
        new_role_id=user.role_id,  # Текущая роль как новая (по умолчанию)
        new_role_name=user.role.role_name
    )

@router.delete("/dell/{user_id}")
async def dell_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_super_admin)
    ) -> dict:
    """Удалить пользователя (только для суперадминов)"""
    # Проверяем существование пользователя
    existing_user = await UsersDAO.find_one_or_none_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Пользователь с ID {user_id} не найден!'
        )

    check = await UsersDAO.delete_user_by_id(user_id=user_id)
    if check:
        return {"message": f"Пользователь с ID {user_id} удален!"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении пользователя!"
        )
    
@router.put("/profile/", summary="Обновить профиль пользователя")
async def update_user_profile(
    profile_data: SUserUpdateProfile,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Обновление имени, фамилии и ника пользователя
    """
    try:
        # Проверяем доступность никнейма
        if profile_data.user_nick != current_user.user_nick:
            nick_available = await UsersDAO.is_nickname_available(
                profile_data.user_nick, 
                current_user.id
            )
            if not nick_available:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Этот никнейм уже занят"
                )
        # ПРОВЕРКА ДОПОЛНИТЕЛЬНОГО EMAIL
        if profile_data.secondary_email:
            # Проверяем, не используется ли email другим пользователем как основной
            existing_user_by_main_email = await UsersDAO.find_by_email(profile_data.secondary_email)
            if existing_user_by_main_email and existing_user_by_main_email.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Этот email уже используется!"
                )
            
            # Проверяем, не используется ли email другим пользователем как дополнительный
            existing_user_by_secondary = await UsersDAO.find_by_secondary_email(profile_data.secondary_email)
            if existing_user_by_secondary and existing_user_by_secondary.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Этот email уже используется!!"
                )
            
            # Проверяем, что дополнительный email не совпадает с основным
            if profile_data.secondary_email == current_user.user_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Дополнительный email не может совпадать с основным"
                )
                
        # Подготавливаем данные для обновления
        update_data = {
            "first_name": profile_data.first_name,
            "last_name": profile_data.last_name,
            "user_nick": profile_data.user_nick,
            "secondary_email": profile_data.secondary_email
        }

        # Обновляем профиль
        # success = await UsersDAO.update_user_profile(
        #     current_user.id,
        #     first_name=profile_data.first_name,
        #     last_name=profile_data.last_name,
        #     user_nick=profile_data.user_nick,
        #     secondary_email=profile_data.secondary_email
        # )

        # Удаляем None значения
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Обновляем пользователя
        success = await UsersDAO.update_user_profile(current_user.id, **update_data)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при обновлении профиля"
            )

        # Логируем изменение
        await UserLogsDAO.create_log(
            user_id=current_user.id,
            action_type='profile_update',
            old_value=json.dumps({
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'user_nick': current_user.user_nick,
                'secondary_email': current_user.secondary_email
            }),
            new_value=json.dumps(update_data),
            description='Обновление основных данных профиля',
            changed_by=current_user.id
        )

        return {"message": "Профиль успешно обновлен"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )
@router.get("/check-secondary-email")
async def check_secondary_email_availability(
    email: str,
    current_user: User = Depends(get_current_user)
):
    """Проверить доступность дополнительного email"""
    try:
        if not email:
            return {"available": True}
            
        # Проверяем формат email
        try:
            from pydantic import EmailStr
            EmailStr._validate(email)
        except:
            return {"available": False, "reason": "invalid_format"}
        
        # Проверяем, не совпадает ли с основным email текущего пользователя
        if email == current_user.user_email:
            return {"available": False, "reason": "same_as_primary"}
        
        # Проверяем, не используется ли email как основной у любого пользователя
        existing_user_by_main_email = await UsersDAO.find_by_email(email)
        if existing_user_by_main_email:
            return {"available": False, "reason": "used_as_primary"}
        
        # Проверяем, не используется ли email как дополнительный у другого пользователя
        existing_user_by_secondary = await UsersDAO.find_by_secondary_email(email)
        if existing_user_by_secondary and existing_user_by_secondary.id != current_user.id:
            return {"available": False, "reason": "used_as_secondary"}
        
        # Если текущий пользователь уже использует этот email как дополнительный - разрешаем
        if existing_user_by_secondary and existing_user_by_secondary.id == current_user.id:
            return {"available": True}
        
        return {"available": True}
        
    except Exception as e:
        logger.error(f"Error checking secondary email availability: {e}")
        return {"available": False, "reason": "server_error"}
    
@router.put("/change-password/", summary="Сменить пароль")
async def change_password(
    password_data: SUserChangePassword,
    current_user: User = Depends(get_current_user)
):
    """
    Смена пароля пользователя
    """
    from app.users.auth import verify_password, get_password_hash
    
    # Проверяем текущий пароль
    if not verify_password(password_data.current_password, current_user.user_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )
    
    # Хешируем новый пароль
    new_hashed_password = get_password_hash(password_data.new_password)
    
    # Обновляем пароль
    success = await UsersDAO.change_password(current_user.id, new_hashed_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при смене пароля"
        )
    
    # Логируем смену пароля
    await UserLogsDAO.create_log(
        user_id=current_user.id,
        action_type='password_change',
        old_value='***',
        new_value='***',
        description='Пароль изменен',
        changed_by=current_user.id
    )
    
    return {"message": "Пароль успешно изменен"}

@router.put("/secondary-email/", summary="Добавить/обновить дополнительный email")
async def add_secondary_email(
    email_data: SUserAddSecondaryEmail,
    current_user: User = Depends(get_current_user)
):
    """
    Добавление дополнительного email
    """
    # Проверяем, не используется ли email другим пользователем
    existing_user = await UsersDAO.find_one_or_none(user_email=email_data.secondary_email)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот email уже используется другим пользователем"
        )
    
    success = await UsersDAO.update_user_profile(
        current_user.id,
        secondary_email=email_data.secondary_email
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении email"
        )
    
    return {"message": "Дополнительный email успешно добавлен"}

@router.post("/ip-restrictions/ip", summary="Добавить IP адрес")
async def add_ip_address(
    ip_data: SUserAddIP,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Добавление разрешенного IP адреса
    """
    
    # Проверяем валидность IP адреса
    if not SecurityUtils.validate_ip_address(ip_data.ip_address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат IP адреса"
        )
    
    # Добавляем IP адрес
    ip_record = await UserAllowedIPsDAO.add_ip_for_user(
        current_user.id,
        ip_data.ip_address,
        ip_data.description
    )
    
    # Логируем добавление IP
    await UserLogsDAO.create_log(
        user_id=current_user.id,
        action_type='ip_added',
        old_value=None,
        new_value=ip_data.ip_address,
        description=f'Добавлен разрешенный IP: {ip_data.ip_address}',
        changed_by=current_user.id
    )
    
    return {
        "message": f"IP адрес {ip_data.ip_address} успешно добавлен",
        "ip_record": {
            "id": ip_record.id,
            "ip_address": ip_record.ip_address,
            "description": ip_record.description
        }
    }

@router.delete("/ip-restrictions/ip", summary="Удалить IP адрес")
async def remove_ip_address(
    ip_data: SUserRemoveIP,
    current_user: User = Depends(get_current_user)
):
    """
    Удаление разрешенного IP адреса
    """
    # Проверяем, существует ли такой IP у пользователя
    existing_ip = await UserAllowedIPsDAO.find_by_ip_and_user(current_user.id, ip_data.ip_address)
    if not existing_ip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP адрес не найден в списке разрешенных"
        )
    
    # Удаляем IP адрес
    success = await UserAllowedIPsDAO.delete_ip(current_user.id, ip_data.ip_address)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении IP адреса"
        )
    
    # Логируем удаление IP
    await UserLogsDAO.create_log(
        user_id=current_user.id,
        action_type='ip_removed',
        old_value=ip_data.ip_address,
        new_value=None,
        description=f'Удален разрешенный IP: {ip_data.ip_address}',
        changed_by=current_user.id
    )
    
    return {"message": f"IP адрес {ip_data.ip_address} удален"}

@router.get("/ip-restrictions/ips", summary="Получить список разрешенных IP", response_model=List[SUserAllowedIPResponse])
async def get_allowed_ips(
    current_user: User = Depends(get_current_user)
):
    """
    Получение списка всех разрешенных IP адресов
    """
    ip_records = await UserAllowedIPsDAO.find_by_user_id(current_user.id, active_only=True)
    return ip_records

@router.post("/ip-restrictions/ips/batch", summary="Добавить несколько IP адресов")
async def add_multiple_ips(
    ip_data: SUserIPRestriction,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Добавление нескольких IP адресов
    """    
    # Валидируем все IP адреса
    for ip_item in ip_data.ip_addresses:
        if not SecurityUtils.validate_ip_address(ip_item.ip_address):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный формат IP адреса: {ip_item.ip_address}"
            )
    
    # Добавляем IP адреса
    added_ips = []
    for ip_item in ip_data.ip_addresses:
        ip_record = await UserAllowedIPsDAO.add_ip_for_user(
            current_user.id,
            ip_item.ip_address,
            ip_item.description
        )
        added_ips.append(ip_record)
    
    # Логируем добавление IP
    await UserLogsDAO.create_log(
        user_id=current_user.id,
        action_type='ips_batch_added',
        old_value=None,
        new_value=json.dumps([ip.ip_address for ip in added_ips]),
        description=f'Добавлено {len(added_ips)} разрешенных IP адресов',
        changed_by=current_user.id
    )
    
    return {
        "message": f"Добавлено {len(added_ips)} IP адресов",
        "added_ips": added_ips
    }

@router.put("/ip-restrictions/ip/{ip_id}", summary="Обновить описание IP адреса")
async def update_ip_description(
    ip_id: int,
    ip_data: SUserAllowedIPBase,
    current_user: User = Depends(get_current_user)
):
    """
    Обновление описания IP адреса
    """
    # Проверяем, принадлежит ли IP пользователю
    ip_record = await UserAllowedIPsDAO.find_one_or_none(id=ip_id, user_id=current_user.id)
    if not ip_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP адрес не найден"
        )
    
    success = await UserAllowedIPsDAO.update_ip_description(
        current_user.id,
        ip_record.ip_address,
        ip_data.description
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении IP адреса"
        )
    
    return {"message": "Описание IP адреса обновлено"}

@router.get("/ip-restrictions/check", summary="Проверить текущий IP")
async def check_current_ip(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Проверка текущего IP адреса
    """
    
    client_ip = SecurityUtils.get_client_ip(request)
    is_allowed = await SecurityUtils.is_ip_allowed(current_user.id, client_ip)
    
    return {
        "ip_address": client_ip,
        "is_allowed": is_allowed,
        "has_restrictions": len(await UserAllowedIPsDAO.find_by_user_id(current_user.id)) > 0
    }

@router.get("/my-profile/", summary="Получить свой профиль", response_model=SUserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Получение полной информации о своем профиле
    """
    user_profile = await UsersDAO.get_user_profile(current_user.id)
    
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден"
        )
    
    return SUserProfileResponse.model_validate(user_profile)

@router.get("/my-ip/", summary="Узнать свой IP адрес")
async def get_my_ip(request: Request):
    """
    Возвращает IP адрес клиента
    """
    from app.utils.secutils import SecurityUtils
    
    client_ip = SecurityUtils.get_client_ip(request)
    return {"ip_address": client_ip}

@router.delete("/secondary-email/", summary="Удалить дополнительный email")
async def remove_secondary_email(
    current_user: User = Depends(get_current_user)
):
    """
    Удаление дополнительного email
    """
    success = await UsersDAO.update_user_profile(
        current_user.id,
        secondary_email=None
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении email"
        )
    
    return {"message": "Дополнительный email удален"}

@router.delete("/ip-restrictions/", summary="Отключить ограничения по IP")
async def disable_ip_restrictions(
    current_user: User = Depends(get_current_user)
):
    """
    Отключение ограничений по IP
    """
    success = await UsersDAO.update_allowed_ips(current_user.id, [])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при отключении ограничений IP"
        )
    
    # Логируем отключение ограничений
    await UserLogsDAO.create_log(
        user_id=current_user.id,
        action_type='ip_restrictions_disable',
        old_value=current_user.allowed_ips or '[]',
        new_value='[]',
        description='Ограничения по IP отключены',
        changed_by=current_user.id
    )
    
    return {"message": "Ограничения по IP отключены"}

@router.post("/logs/cleanup", summary="Очистить старые логи")
async def cleanup_old_logs(
    days_to_keep: int = 30,
    current_user: User = Depends(get_current_admin)
):
    """
    Ручная очистка логов старше указанного количества дней
    """
    if days_to_keep < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Количество дней должно быть положительным числом"
        )
    
    try:
        deleted_count = await LogCleaner.cleanup_old_logs(days_to_keep)
        
        # Логируем действие администратора
        await UserLogsDAO.create_log(
            user_id=current_user.id,
            action_type='logs_cleanup',
            old_value=None,
            new_value=str(deleted_count),
            description=f'Администратор выполнил очистку логов старше {days_to_keep} дней. Удалено записей: {deleted_count}',
            changed_by=current_user.id
        )
        
        return {
            "message": f"Удалено {deleted_count} записей логов старше {days_to_keep} дней",
            "deleted_count": deleted_count,
            "days_to_keep": days_to_keep
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при очистке логов: {str(e)}"
        )

@router.get("/logs/statistics", summary="Статистика логов")
async def get_logs_statistics(
    current_user: User = Depends(get_current_admin)
):
    """
    Получение статистики по логам
    """
    statistics = await LogCleaner.get_log_statistics()
    return statistics

@router.get("/logs/cleanup/status", summary="Статус фоновой очистки")
async def get_cleanup_status(
    current_user: User = Depends(get_current_admin)
):
    """
    Получение статуса фоновой задачи очистки
    """
    return {
        "is_running": background_tasks.is_running,
        "cleanup_interval_hours": background_tasks.cleanup_interval / 3600
    }

@router.post("/logs/cleanup/start", summary="Запустить фоновую очистку")
async def start_background_cleanup(
    current_user: User = Depends(get_current_admin)
):
    """
    Запуск фоновой задачи очистки логов
    """
    if background_tasks.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Фоновая очистка уже запущена"
        )
    
    asyncio.create_task(background_tasks.start_cleanup_task())
    
    await UserLogsDAO.create_log(
        user_id=current_user.id,
        action_type='background_cleanup_start',
        old_value="stopped",
        new_value="started",
        description='Администратор запустил фоновую очистку логов',
        changed_by=current_user.id
    )
    
    return {"message": "Фоновая очистка логов запущена"}

@router.post("/logs/cleanup/stop", summary="Остановить фоновую очистку")
async def stop_background_cleanup(
    current_user: User = Depends(get_current_admin)
):
    """
    Остановка фоновой задачи очистки логов
    """
    if not background_tasks.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Фоновая очистка не запущена"
        )
    
    background_tasks.stop_cleanup_task()
    
    await UserLogsDAO.create_log(
        user_id=current_user.id,
        action_type='background_cleanup_stop',
        old_value="started",
        new_value="stopped",
        description='Администратор остановил фоновую очистку логов',
        changed_by=current_user.id
    )
    
    return {"message": "Фоновая очистка логов остановлена"}

# Новые эндпоинты для управления очисткой логов
@router.post("/admin/logs/cleanup-now", summary="Ручная очистка старых логов")
async def cleanup_logs_now(
    days_to_keep: Optional[int] = None,
    current_user: User = Depends(get_current_admin)
):
    """
    Ручной запуск очистки логов старше указанного количества дней
    """
    try:
        # Если указано количество дней, временно меняем настройку
        original_days = log_cleanup.cleanup_days
        if days_to_keep is not None:
            if days_to_keep < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Количество дней должно быть положительным числом"
                )
            log_cleanup.cleanup_days = days_to_keep

        deleted_count = await log_cleanup.run_cleanup()
        
        # Возвращаем оригинальные настройки
        if days_to_keep is not None:
            log_cleanup.cleanup_days = original_days
        
        # Логируем действие администратора
        await UserLogsDAO.create_log(
            user_id=current_user.id,
            action_type='manual_logs_cleanup',
            old_value=None,
            new_value=str(deleted_count),
            description=f'Администратор выполнил ручную очистку логов. Удалено: {deleted_count} записей',
            changed_by=current_user.id
        )
        
        logger.info(f"Администратор {current_user.user_email} выполнил очистку логов")
        
        return {
            "message": f"Очистка завершена. Удалено {deleted_count} записей",
            "deleted_count": deleted_count,
            "days_to_keep": days_to_keep or original_days
        }
        
    except Exception as e:
        logger.error(f"Ошибка при ручной очистке логов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка очистки: {str(e)}"
        )

@router.get("/admin/logs/cleanup-status", summary="Статус задачи очистки логов")
async def get_cleanup_status(
    current_user: User = Depends(get_current_admin)
):
    """
    Получение статуса фоновой задачи очистки логов
    """
    logger.info(f"Администратор {current_user.user_email} запросил статус очистки")
    
    return {
        "is_running": log_cleanup.is_running,
        "cleanup_days": log_cleanup.cleanup_days,
        "interval_hours": log_cleanup.interval_hours,
        "description": f"Автоматическая очистка логов старше {log_cleanup.cleanup_days} дней"
    }

@router.post("/admin/logs/cleanup/start", summary="Запуск фоновой очистки")
async def start_background_cleanup(
    current_user: User = Depends(get_current_admin)
):
    """
    Запуск фоновой задачи очистки логов
    """
    if log_cleanup.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Фоновая очистка уже запущена"
        )
    
    # Запускаем в фоне
    asyncio.create_task(log_cleanup.start_periodic_cleanup())
    
    # Логируем действие
    await UserLogsDAO.create_log(
        user_id=current_user.id,
        action_type='background_cleanup_start',
        old_value="stopped",
        new_value="started",
        description='Администратор запустил фоновую очистку логов',
        changed_by=current_user.id
    )
    
    logger.info(f"Администратор {current_user.user_email} запустил фоновую очистку")
    
    return {"message": "Фоновая очистка логов запущена"}

@router.post("/admin/logs/cleanup/stop", summary="Остановка фоновой очистки")
async def stop_background_cleanup(
    current_user: User = Depends(get_current_admin)
):
    """
    Остановка фоновой задачи очистки логов
    """
    if not log_cleanup.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Фоновая очистка не запущена"
        )
    
    log_cleanup.stop()
    
    # Логируем действие
    await UserLogsDAO.create_log(
        user_id=current_user.id,
        action_type='background_cleanup_stop',
        old_value="started",
        new_value="stopped",
        description='Администратор остановил фоновую очистку логов',
        changed_by=current_user.id
    )
    
    logger.info(f"Администратор {current_user.user_email} остановил фоновую очистку")
    
    return {"message": "Фоновая очистка логов остановлена"}

@router.put("/admin/logs/cleanup/settings", summary="Настройка очистки логов")
async def update_cleanup_settings(
    cleanup_days: Optional[int] = None,
    interval_hours: Optional[int] = None,
    current_user: User = Depends(get_current_admin)
):
    """
    Обновление настроек очистки логов
    """
    old_settings = {
        "cleanup_days": log_cleanup.cleanup_days,
        "interval_hours": log_cleanup.interval_hours
    }
    
    # Обновляем настройки если переданы
    if cleanup_days is not None:
        if cleanup_days < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Количество дней должно быть положительным числом"
            )
        log_cleanup.cleanup_days = cleanup_days
    
    if interval_hours is not None:
        if interval_hours < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Интервал должен быть положительным числом"
            )
        log_cleanup.interval_hours = interval_hours
    
    new_settings = {
        "cleanup_days": log_cleanup.cleanup_days,
        "interval_hours": log_cleanup.interval_hours
    }
    
    # Логируем изменение настроек
    await UserLogsDAO.create_log(
        user_id=current_user.id,
        action_type='cleanup_settings_update',
        old_value=json.dumps(old_settings),
        new_value=json.dumps(new_settings),
        description='Администратор обновил настройки очистки логов',
        changed_by=current_user.id
    )
    
    logger.info(f"Администратор {current_user.user_email} обновил настройки очистки: {new_settings}")
    
    return {
        "message": "Настройки очистки логов обновлены",
        "old_settings": old_settings,
        "new_settings": new_settings
    }

@router.get("/check-nickname")
async def check_nickname_availability(
    nick: str,
    current_user: User = Depends(get_current_user)
):
    """Проверить доступность никнейма"""
    is_available = await UsersDAO.is_nickname_available(nick, current_user.id)
    return {"available": is_available}