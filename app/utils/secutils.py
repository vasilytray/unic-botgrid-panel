import ipaddress
import json
from typing import List, Optional, Dict, Any
from fastapi import Request
from datetime import datetime, timezone
from app.users.ip_dao import UserAllowedIPsDAO

class SecurityUtils:
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Получает реальный IP адрес клиента"""
        if "x-forwarded-for" in request.headers:
            ip = request.headers["x-forwarded-for"].split(",")[0]
        elif "x-real-ip" in request.headers:
            ip = request.headers["x-real-ip"]
        else:
            ip = request.client.host
        
        return ip.strip()
    
    @staticmethod
    async def is_ip_allowed(user_id: int, client_ip: str) -> bool:
        """Проверяет, разрешен ли IP адрес для пользователя"""
        # Если у пользователя нет ограничений по IP, разрешаем доступ
        user_ips = await UserAllowedIPsDAO.find_by_user_id(user_id, active_only=True)
        if not user_ips:
            return True
        
        return await UserAllowedIPsDAO.is_ip_allowed(user_id, client_ip)
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Валидирует IP адрес"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_ip_restrictions(ip_list: List[str]) -> bool:
        """Валидирует список IP адресов"""
        for ip in ip_list:
            if not SecurityUtils.validate_ip_address(ip):
                return False
        return True