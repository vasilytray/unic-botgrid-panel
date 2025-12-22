# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from typing import Optional, List
import json
import asyncio
import re
import random
from datetime import datetime
from pydantic import EmailStr, ValidationError

from app.core.security import (
    get_password_hash, 
    authenticate_user, 
    create_access_token
)
from app.core.dependencies import (
    get_current_user, 
    get_current_admin, 
    get_current_super_admin,
    validate_role_change,
    log_role_change,
    get_user_dao,
    get_user_logs_dao,
    get_redis_dao
)
from app.dao.users import UserDAO, UserLogsDAO
from app.dao.roles import RoleDAO
from app.dao.redis import RedisDAO
from app.models.users import User
from app.utils.secutils import SecurityUtils
from app.users.log_cleaner import LogCleaner
from app.users.ip_dao import UserAllowedIPsDAO

# from app.users.schemas import (
#     SUserRegister, SUserAuth, SUserResponse, SUserListResponse,
#     SUserUpdateProfile, SUserChangePassword, SUserAddSecondaryEmail,
#     SUserAddIP, SUserRemoveIP, SUserAllowedIPResponse, SUserIPRestriction,
#     SUserProfileResponse, SUserUpdateRole, SUserUpdateRoleResponse,
#     SUserUpdateRoleByEmail, SUserLogResponse, SUserLogsList, SRoleChangeLog,
#     SUserAdd, SUserByEmailResponse, SUserRoleInfo
# )

from app.schemas.users import (
    SUserRegister, SUserAuth, SUserResponse, SUserListResponse,
    SUserUpdateProfile, SUserChangePassword, SUserAddSecondaryEmail,
    SUserAddIP, SUserRemoveIP, SUserAllowedIPResponse, SUserIPRestriction,
    SUserProfileResponse, SUserUpdateRole, SUserUpdateRoleResponse,
    SUserUpdateRoleByEmail, SUserLogResponse, SUserLogsList, SRoleChangeLog,
    SUserAdd, SUserByEmailResponse, SUserRoleInfo
)

router = APIRouter(prefix="/users", tags=["users"])

# Вспомогательные функции
def _create_base_nick(first_name: str, last_name: str) -> str:
    """Создает базовый никнейм из имени и фамилии"""
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

async def generate_unique_nick(first_name: str, last_name: str, user_dao: UserDAO) -> str:
    """Генерирует уникальный никнейм"""
    base_nick = _create_base_nick(first_name, last_name)
    unique_nick = base_nick
    counter = 1
    
    while counter <= 100:
        existing_user = await user_dao.find_one_or_none(user_nick=unique_nick)
        if not existing_user:
            break
        
        if counter == 1:
            unique_nick = f"{base_nick}_{counter}"
        else:
            max_base_length = 47 - len(str(counter))
            truncated_base = base_nick[:max_base_length]
            unique_nick = f"{truncated_base}_{counter}"
        
        counter += 1
    
    if counter > 100:
        unique_nick = f"user_{random.randint(10000, 99999)}"
    
    return unique_nick

def validate_email_format(email: str) -> bool:
    """Валидация формата email"""
    try:
        # Используем Pydantic для валидации email
        EmailStr._validate(email)  # type: ignore
        return True
    except ValidationError:
        return False

# Роуты аутентификации
@router.post("/register/", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: SUserRegister) -> dict:
    """Регистрация нового пользователя"""
    user_dao = UserDAO()
    
    # Проверяем существование пользователя по email
    existing_user = await user_dao.get_user_by_email(user_data.user_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким email уже существует'
        )
    
    # Проверяем существование пользователя по телефону
    existing_user = await user_dao.get_user_by_phone(user_data.user_phone)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким телефоном уже существует'
        )

    # Генерируем уникальный ник, если не указан
    user_dict = user_data.model_dump(exclude={'user_pass_check'})
    
    if not user_dict.get('user_nick'):
        user_dict['user_nick'] = await generate_unique_nick(
            user_data.first_name, 
            user_data.last_name,
            user_dao
        )

    user_dict['user_pass'] = get_password_hash(user_data.user_pass)
    
    user_id = await user_dao.add(**user_dict)
    return {'message': 'Вы успешно зарегистрированы!', 'user_id': user_id}

@router.post("/login/")
async def auth_user(
    response: Response, 
    user_data: SUserAuth, 
    request: Request
):
    """Аутентификация пользователя"""
    check = await authenticate_user(
        user_email=user_data.user_email, 
        user_pass=user_data.user_pass,
        request=request
    )
    
    if check is None:
        from app.exceptions import IncorrectEmailOrPasswordException
        raise IncorrectEmailOrPasswordException
    
    # Обновляем время последнего входа
    user_dao = UserDAO()
    success = await user_dao.update_last_login(check.id)
    
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(
        key="users_access_token", 
        value=access_token, 
        httponly=True,
        max_age=30*24*60*60,
        path="/"
    )
    
    # Логируем успешный вход
    user_logs_dao = UserLogsDAO()
    client_ip = SecurityUtils.get_client_ip(request)
    await user_logs_dao.create_user_log(
        user_id=check.id,
        action_type='login',
        old_value=None,
        new_value=f"ip:{client_ip}",
        description=f'Успешный вход в систему с IP {client_ip}',
        changed_by=check.id
    )
    
    return {
        "ok": True,
        "message": "Авторизация успешна!",
        "redirect_url": "/lk/plist",
        "user_id": check.id,
        "user_name": f"{check.first_name} {check.last_name}",
        "ip_address": client_ip
    }

@router.post("/logout/")
async def logout_user(response: Response):
    """Выход из системы"""
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}

# Роуты получения информации о пользователях
@router.get("/me/", response_model=SUserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    user_dao = UserDAO()
    user_profile = await user_dao.get_user_profile(current_user.id)
    
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден"
        )
    
    return SUserProfileResponse(**user_profile)

@router.get("/", response_model=SUserListResponse)
async def get_all_users(
    current_user: User = Depends(get_current_admin),
    skip: int = 0,
    limit: int = 100
):
    """Получить список всех пользователей (только для админов)"""
    user_dao = UserDAO()
    users = await user_dao.get_all_users_with_roles(skip=skip, limit=limit)
    
    return SUserListResponse(
        users=[SUserResponse.model_validate(user) for user in users],
        total=len(users)
    )

@router.get("/{user_id}", response_model=SUserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin)
):
    """Получить пользователя по ID (только для админов)"""
    user_dao = UserDAO()
    user_data = await user_dao.get_user_with_role(user_id)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Пользователь с ID {user_id} не найден!'
        )
    
    return SUserResponse.model_validate(user_data)

@router.get("/by-email/", response_model=SUserByEmailResponse)
async def get_user_by_email(
    email: str,
    current_user: User = Depends(get_current_user)
):
    """Получить пользователя по email"""
    user_dao = UserDAO()
    
    # Проверяем права доступа
    if not current_user.is_admin and current_user.user_email != email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете просматривать только свою информацию"
        )
    
    user_data = await user_dao.get_user_by_email(email)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Пользователь с email {email} не найден!'
        )
    
    return SUserByEmailResponse.model_validate(user_data)

# Роуты управления пользователями (админские)
@router.post("/add/")
async def add_user(
    user: SUserAdd,
    current_user: User = Depends(get_current_admin)
) -> dict:
    """Добавить пользователя (только для админов)"""
    user_dao = UserDAO()
    
    # Проверяем уникальность email
    existing_user = await user_dao.get_user_by_email(user.user_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким email уже существует'
        )
    
    # Проверяем уникальность телефона
    existing_user = await user_dao.get_user_by_phone(user.user_phone)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким телефоном уже существует'
        )

    user_data = user.model_dump()
    user_data['user_pass'] = get_password_hash(user_data['user_pass'])
    
    user_id = await user_dao.add(**user_data)
    if user_id:
        return {"message": "Пользователь успешно добавлен!", "user_id": user_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при добавлении пользователя!"
        )

@router.put("/update-role/", response_model=SUserUpdateRoleResponse)
async def update_user_role(
    role_data: SUserUpdateRole,
    super_admin: User = Depends(get_current_super_admin)
):
    """Изменить роль пользователя по ID (только для суперадмина)"""
    user_dao = UserDAO()
    role_dao = RoleDAO()
    
    # Валидация изменения роли
    target_user = await validate_role_change(super_admin, role_data.user_id, role_data.new_role_id)
    
    # Проверяем существование новой роли
    new_role = await role_dao.find_by_id(role_data.new_role_id)
    if not new_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Роль с ID {role_data.new_role_id} не найдена"
        )
    
    # Сохраняем старую роль
    old_role_id = target_user.role_id
    
    # Обновляем роль
    success = await user_dao.update_user_role(role_data.user_id, role_data.new_role_id)
    
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

@router.put("/update-role-by-email/", response_model=SUserUpdateRoleResponse)
async def update_user_role_by_email(
    role_data: SUserUpdateRoleByEmail,
    super_admin: User = Depends(get_current_super_admin)
):
    """Изменить роль пользователя по email (только для суперадмина)"""
    user_dao = UserDAO()
    role_dao = RoleDAO()
    
    # Находим пользователя по email
    target_user = await user_dao.get_user_by_email(role_data.user_email)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с email {role_data.user_email} не найден"
        )
    
    # Валидация изменения роли
    await validate_role_change(super_admin, target_user.id, role_data.new_role_id)
    
    # Проверяем существование новой роли
    new_role = await role_dao.find_by_id(role_data.new_role_id)
    if not new_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Роль с ID {role_data.new_role_id} не найдена"
        )
    
    # Сохраняем старую роль
    old_role_id = target_user.role_id
    
    # Обновляем роль
    success = await user_dao.update_user_role(target_user.id, role_data.new_role_id)
    
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

@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_super_admin)
) -> dict:
    """Удалить пользователя (только для суперадминов)"""
    user_dao = UserDAO()
    
    # Проверяем существование пользователя
    existing_user = await user_dao.get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Пользователь с ID {user_id} не найден!'
        )

    success = await user_dao.delete(id=user_id)
    if success:
        return {"message": f"Пользователь с ID {user_id} удален!"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении пользователя!"
        )

# Роуты управления профилем
@router.put("/profile/")
async def update_user_profile(
    profile_data: SUserUpdateProfile,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Обновление профиля пользователя"""
    user_dao = UserDAO()
    user_logs_dao = UserLogsDAO()
    
    try:
        # Проверяем доступность никнейма
        if profile_data.user_nick != current_user.user_nick:
            nick_available = await user_dao.is_nickname_available(
                profile_data.user_nick, 
                current_user.id
            )
            if not nick_available:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Этот никнейм уже занят"
                )
        
        # Проверяем дополнительный email
        if profile_data.secondary_email:
            # Проверяем, не используется ли email другим пользователем как основной
            existing_user_by_main_email = await user_dao.get_user_by_email(profile_data.secondary_email)
            if existing_user_by_main_email and existing_user_by_main_email.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Этот email уже используется!"
                )
            
            # Проверяем, не используется ли email другим пользователем как дополнительный
            existing_user_by_secondary = await user_dao.find_one_or_none(secondary_email=profile_data.secondary_email)
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

        # Удаляем None значения
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Обновляем пользователя
        success = await user_dao.update_user_profile(current_user.id, **update_data)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при обновлении профиля"
            )

        # Логируем изменение
        await user_logs_dao.create_user_log(
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@router.put("/change-password/")
async def change_password(
    password_data: SUserChangePassword,
    current_user: User = Depends(get_current_user)
):
    """Смена пароля пользователя"""
    user_dao = UserDAO()
    user_logs_dao = UserLogsDAO()
    
    from app.core.security import verify_password, get_password_hash
    
    # Проверяем текущий пароль
    if not verify_password(password_data.current_password, current_user.user_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )
    
    # Хешируем новый пароль
    new_hashed_password = get_password_hash(password_data.new_password)
    
    # Обновляем пароль
    success = await user_dao.change_password(current_user.id, new_hashed_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при смене пароля"
        )
    
    # Логируем смену пароля
    await user_logs_dao.create_user_log(
        user_id=current_user.id,
        action_type='password_change',
        old_value='***',
        new_value='***',
        description='Пароль изменен',
        changed_by=current_user.id
    )
    
    return {"message": "Пароль успешно изменен"}

# Роуты управления IP адресами
@router.post("/ip-restrictions/ip")
async def add_ip_address(
    ip_data: SUserAddIP,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Добавление разрешенного IP адреса"""
    ip_dao = UserAllowedIPsDAO()
    
    # Проверяем валидность IP адреса
    if not SecurityUtils.validate_ip_address(ip_data.ip_address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат IP адреса"
        )
    
    # Исправление: преобразуем Optional[str] в str для description
    description_str = ip_data.description or ""
    
    # Добавляем IP адрес
    ip_record = await ip_dao.add_ip_for_user(
        current_user.id,
        ip_data.ip_address,
        description_str  # Теперь это точно str, а не Optional[str]
    )
    
    # Логируем добавление IP
    user_logs_dao = UserLogsDAO()
    await user_logs_dao.create_user_log(
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

@router.delete("/ip-restrictions/ip")
async def remove_ip_address(
    ip_data: SUserRemoveIP,
    current_user: User = Depends(get_current_user)
):
    """Удаление разрешенного IP адреса"""
    ip_dao = UserAllowedIPsDAO()
    
    # Проверяем, существует ли такой IP у пользователя
    existing_ip = await ip_dao.find_by_ip_and_user(current_user.id, ip_data.ip_address)
    if not existing_ip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP адрес не найден в списке разрешенных"
        )
    
    # Удаляем IP адрес
    success = await ip_dao.delete_ip(current_user.id, ip_data.ip_address)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении IP адреса"
        )
    
    # Логируем удаление IP
    user_logs_dao = UserLogsDAO()
    await user_logs_dao.create_user_log(
        user_id=current_user.id,
        action_type='ip_removed',
        old_value=ip_data.ip_address,
        new_value=None,
        description=f'Удален разрешенный IP: {ip_data.ip_address}',
        changed_by=current_user.id
    )
    
    return {"message": f"IP адрес {ip_data.ip_address} удален"}

@router.get("/ip-restrictions/ips", response_model=List[SUserAllowedIPResponse])
async def get_allowed_ips(
    current_user: User = Depends(get_current_user)
):
    """Получение списка всех разрешенных IP адресов"""
    ip_dao = UserAllowedIPsDAO()
    ip_records = await ip_dao.find_by_user_id(current_user.id, active_only=True)
    return ip_records

@router.get("/ip-restrictions/check")
async def check_current_ip(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Проверка текущего IP адреса"""
    client_ip = SecurityUtils.get_client_ip(request)
    is_allowed = await SecurityUtils.is_ip_allowed(current_user.id, client_ip)
    
    return {
        "ip_address": client_ip,
        "is_allowed": is_allowed,
        "has_restrictions": len(await UserAllowedIPsDAO().find_by_user_id(current_user.id)) > 0
    }

# Роуты для работы с логами
@router.get("/logs/", response_model=SUserLogsList)
async def get_users_logs(
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    admin_user: User = Depends(get_current_super_admin)
):
    """Получить логи пользователей (только для суперадминов)"""
    user_logs_dao = UserLogsDAO()
    
    # Собираем фильтры
    filters = {}
    if user_id:
        filters['user_id'] = user_id
    if action_type:
        filters['action_type'] = action_type
    
    # Получаем логи
    logs = await user_logs_dao.find_all(**filters)
    
    # Сортируем и ограничиваем результат
    sorted_logs = sorted(logs, key=lambda x: x.created_at, reverse=True)
    paginated_logs = sorted_logs[offset:offset + limit]
    
    # Преобразуем в схему ответа
    log_responses = []
    for log in paginated_logs:
        # Получаем связанные данные пользователей
        user_dao = UserDAO()
        user = await user_dao.get_user_by_id(log.user_id) if log.user_id else None
        changer = await user_dao.get_user_by_id(log.changed_by) if log.changed_by else None
        
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

@router.get("/logs/role-changes/", response_model=List[SRoleChangeLog])
async def get_role_change_logs(
    user_id: Optional[int] = None,
    days: int = 30,
    admin_user: User = Depends(get_current_super_admin)
):
    """Получить логи изменений ролей (только для суперадминов)"""
    user_logs_dao = UserLogsDAO()
    logs = await user_logs_dao.get_recent_role_changes(days=days)
    
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

# Вспомогательные роуты
@router.get("/check-nickname")
async def check_nickname_availability(
    nick: str,
    current_user: User = Depends(get_current_user)
):
    """Проверить доступность никнейма"""
    user_dao = UserDAO()
    is_available = await user_dao.is_nickname_available(nick, current_user.id)
    return {"available": is_available}

@router.get("/check-secondary-email")
async def check_secondary_email_availability(
    email: str,
    current_user: User = Depends(get_current_user)
):
    """Проверить доступность дополнительного email"""
    user_dao = UserDAO()
    
    try:
        if not email:
            return {"available": True}
            
        # Исправление: используем нашу функцию валидации вместо прямого вызова _validate
        if not validate_email_format(email):
            return {"available": False, "reason": "invalid_format"}
        
        # Проверяем, не совпадает ли с основным email текущего пользователя
        if email == current_user.user_email:
            return {"available": False, "reason": "same_as_primary"}
        
        # Проверяем, не используется ли email как основной у любого пользователя
        existing_user_by_main_email = await user_dao.get_user_by_email(email)
        if existing_user_by_main_email:
            return {"available": False, "reason": "used_as_primary"}
        
        # Проверяем, не используется ли email как дополнительный у другого пользователя
        existing_user_by_secondary = await user_dao.find_one_or_none(secondary_email=email)
        if existing_user_by_secondary and existing_user_by_secondary.id != current_user.id:
            return {"available": False, "reason": "used_as_secondary"}
        
        # Если текущий пользователь уже использует этот email как дополнительный - разрешаем
        if existing_user_by_secondary and existing_user_by_secondary.id == current_user.id:
            return {"available": True}
        
        return {"available": True}
        
    except Exception as e:
        return {"available": False, "reason": "server_error"}

@router.get("/my-ip/")
async def get_my_ip(request: Request):
    """Возвращает IP адрес клиента"""
    client_ip = SecurityUtils.get_client_ip(request)
    return {"ip_address": client_ip}

@router.get("/available-roles/")
async def get_available_roles(
    super_admin: User = Depends(get_current_super_admin)
) -> List[dict]:
    """Получить список доступных ролей для назначения"""
    role_dao = RoleDAO()
    roles = await role_dao.get_available_roles(exclude_super_admin=True)
    
    return [
        {
            "id": role.id,
            "name": role.role_name,
            "description": role.role_description,
            "user_count": role.count_users
        }
        for role in roles
    ]

@router.get("/{user_id}/role-info", response_model=SUserRoleInfo)
async def get_user_role_info(
    user_id: int,
    super_admin: User = Depends(get_current_super_admin)
):
    """Получить подробную информацию о роли пользователя"""
    user_dao = UserDAO()
    user = await user_dao.get_user_with_role(user_id)
    
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
        new_role_id=user.role_id,
        new_role_name=user.role.role_name
    )