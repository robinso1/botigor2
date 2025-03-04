import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Хранилище для отслеживания активности пользователей
user_activity = defaultdict(list)
spam_warnings = defaultdict(int)
blocked_users = set()

# Настройки антиспама
MAX_REQUESTS_PER_MINUTE = 10
MAX_WARNINGS = 3
BLOCK_DURATION_HOURS = 24

def check_spam(user_id: int, current_time: datetime = None) -> bool:
    """
    Проверяет активность пользователя на предмет спама
    
    Args:
        user_id (int): ID пользователя
        current_time (datetime, optional): Текущее время
    
    Returns:
        bool: True если обнаружен спам, False в противном случае
    """
    if user_id in blocked_users:
        return True
    
    if current_time is None:
        current_time = datetime.utcnow()
    
    # Очищаем старые записи
    user_activity[user_id] = [
        time for time in user_activity[user_id]
        if current_time - time < timedelta(minutes=1)
    ]
    
    # Добавляем новую активность
    user_activity[user_id].append(current_time)
    
    # Проверяем количество запросов за последнюю минуту
    if len(user_activity[user_id]) > MAX_REQUESTS_PER_MINUTE:
        spam_warnings[user_id] += 1
        logger.warning(f"Спам-предупреждение для пользователя {user_id}: {spam_warnings[user_id]}/{MAX_WARNINGS}")
        
        if spam_warnings[user_id] >= MAX_WARNINGS:
            blocked_users.add(user_id)
            logger.warning(f"Пользователь {user_id} заблокирован за спам")
            return True
        
        return True
    
    return False

def encrypt_personal_data(data: str) -> str:
    """
    Шифрует персональные данные
    
    Args:
        data (str): Данные для шифрования
    
    Returns:
        str: Зашифрованные данные
    """
    if not data:
        return ""
    
    # Используем SHA-256 для хеширования
    return hashlib.sha256(data.encode()).hexdigest()

def mask_phone_number(phone: str, mask_percent: int = 60) -> str:
    """
    Маскирует номер телефона
    
    Args:
        phone (str): Номер телефона
        mask_percent (int): Процент маскировки
    
    Returns:
        str: Замаскированный номер
    """
    if not phone:
        return ""
    
    # Удаляем все нецифровые символы
    digits = ''.join(filter(str.isdigit, phone))
    
    if not digits:
        return phone
    
    # Вычисляем количество символов для маскировки
    mask_length = int(len(digits) * mask_percent / 100)
    start_visible = (len(digits) - mask_length) // 2
    end_visible = len(digits) - start_visible - mask_length
    
    # Формируем маскированный номер
    masked = digits[:start_visible] + '*' * mask_length + digits[-end_visible:] if end_visible > 0 else digits[:start_visible] + '*' * mask_length
    
    # Форматируем номер в читаемый вид
    if len(masked) == 11:  # Для российских номеров
        return f"+{masked[0]} ({masked[1:4]}) {masked[4:7]}-{masked[7:9]}-{masked[9:]}"
    return masked

def log_security_event(event_type: str, user_id: int, details: Dict[str, Any]) -> None:
    """
    Записывает событие безопасности в журнал
    
    Args:
        event_type (str): Тип события
        user_id (int): ID пользователя
        details (Dict[str, Any]): Детали события
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "details": details
    }
    logger.info(f"Security event: {json.dumps(event)}")

def verify_user_access(user_id: int, required_role: str = None) -> bool:
    """
    Проверяет права доступа пользователя
    
    Args:
        user_id (int): ID пользователя
        required_role (str, optional): Требуемая роль
    
    Returns:
        bool: True если доступ разрешен, False в противном случае
    """
    if user_id in blocked_users:
        return False
    
    # Проверяем роль, если она указана
    if required_role == "admin":
        from config import ADMIN_IDS
        return user_id in ADMIN_IDS
    
    return True 