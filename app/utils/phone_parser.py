import re
from typing import Optional


class PhoneParser:
    """Парсер телефонных номеров"""
    
    @staticmethod
    def normalize_phone(phone: str) -> Optional[str]:
        """
        Нормализует номер телефона в международный формат
        
        Примеры:
        +7 (987) 654-32-10 -> +79876543210
        8 (987) 654-32-10 -> +79876543210
        89876543210 -> +79876543210
        9876543210 -> +79876543210
        """
        if not phone:
            return None
            
        # Удаляем все нецифровые символы
        digits = re.sub(r'\D', '', phone)
        
        if not digits:
            return None
        
        # Обрабатываем российские номера
        if digits.startswith('8') and len(digits) == 11:
            # Номер вида 89876543210
            return '+7' + digits[1:]
        elif digits.startswith('7') and len(digits) == 11:
            # Номер вида 79876543210
            return '+' + digits
        elif len(digits) == 10:
            # Номер вида 9876543210
            return '+7' + digits
        elif digits.startswith('+') and len(digits) >= 11:
            # Уже в международном формате
            return '+' + digits[1:]
        else:
            # Для других случаев возвращаем как есть (после очистки)
            return '+' + digits if not digits.startswith('+') else digits
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Проверяет валидность номера телефона"""
        normalized = PhoneParser.normalize_phone(phone)
        if not normalized:
            return False
        
        # Проверяем формат: + и от 10 до 15 цифр
        return bool(re.match(r'^\+\d{10,15}$', normalized))
    
    @staticmethod
    def format_phone_display(phone: str) -> str:
        """Форматирует номер для красивого отображения"""
        normalized = PhoneParser.normalize_phone(phone)
        if not normalized:
            return phone
        
        # Форматируем российские номера
        if normalized.startswith('+7') and len(normalized) == 12:
            # +79876543210 -> +7 (987) 654-32-10
            return f"+7 ({normalized[2:5]}) {normalized[5:8]}-{normalized[8:10]}-{normalized[10:12]}"
        
        return normalized