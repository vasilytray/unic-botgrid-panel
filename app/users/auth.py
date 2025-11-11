from passlib.context import CryptContext
from fastapi import status, HTTPException, Request
from pydantic import EmailStr
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.config import get_auth_data
from app.users.dao import UsersDAO
from app.utils.secutils import SecurityUtils


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    auth_data = get_auth_data()
    encode_jwt = jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])
    return encode_jwt

# async def authenticate_user(user_email: EmailStr, user_pass: str):
#     user = await UsersDAO.find_one_or_none(user_email=user_email)
#     if not user or verify_password(plain_password=user_pass, hashed_password=user.user_pass) is False:
#         return None
#     return user

async def authenticate_user(user_email: EmailStr, user_pass: str, request: Request = None):
    user = await UsersDAO.find_one_or_none(user_email=user_email)
    if not user or verify_password(plain_password=user_pass, hashed_password=user.user_pass) is False:
        return None
    
    # Проверяем IP если есть ограничения
    if request:
        client_ip = SecurityUtils.get_client_ip(request)
        if not await SecurityUtils.is_ip_allowed(user.id, client_ip):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ с IP {client_ip} запрещен"
            )
    
    return user