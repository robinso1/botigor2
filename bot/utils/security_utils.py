import logging
import json
import hashlib
import base64
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from cryptography.fernet import Fernet
import os
from config import SECRET_KEY, MAX_REQUESTS_PER_MINUTE, MAX_WARNINGS, BLOCK_DURATION_HOURS, ADMIN_IDS

logger = logging.getLogger(__name__)

# Словарь для хранения временных данных о запросах пользователей
# {user_id: {'requests': [timestamp1, timestamp2, ...], 'warnings': 0, 'blocked_until': datetime}}
user_requests = {}

def check_spam(user_id: int, current_time: datetime = None) -> bool:
    """
    Проверяет, не превышает ли пользователь лимит запросов в минуту
    
    Args:
        user_id: ID пользователя
        current_time: Текущее время (для тестирования)
        
    Returns:
        bool: True если пользователь превышает лимит, False в противном случае
    """
    if user_id in ADMIN_IDS:
        return False  # Администраторы не подлежат проверке на спам
        
    if current_time is None:
        current_time = datetime.now()
        
    # Инициализируем данные пользователя, если их нет
    if user_id not in user_requests:
        user_requests[user_id] = {
            'requests': [],
            'warnings': 0,
            'blocked_until': None
        }
        
    user_data = user_requests[user_id]
    
    # Проверяем, не заблокирован ли пользователь
    if user_data['blocked_until'] and user_data['blocked_until'] > current_time:
        return True
        
    # Удаляем устаревшие запросы (старше 1 минуты)
    one_minute_ago = current_time - timedelta(minutes=1)
    user_data['requests'] = [ts for ts in user_data['requests'] if ts > one_minute_ago]
    
    # Добавляем текущий запрос
    user_data['requests'].append(current_time)
    
    # Проверяем, не превышен ли лимит
    if len(user_data['requests']) > MAX_REQUESTS_PER_MINUTE:
        user_data['warnings'] += 1
        
        # Если превышено максимальное количество предупреждений, блокируем пользователя
        if user_data['warnings'] >= MAX_WARNINGS:
            user_data['blocked_until'] = current_time + timedelta(hours=BLOCK_DURATION_HOURS)
            logger.warning(f"Пользователь {user_id} заблокирован до {user_data['blocked_until']}")
            
        return True
        
    return False

def encrypt_personal_data(data: str) -> str:
    """
    Шифрует персональные данные
    
    Args:
        data: Строка с персональными данными
        
    Returns:
        str: Зашифрованная строка в формате base64
    """
    if not data:
        return ""
        
    try:
        # Создаем ключ на основе SECRET_KEY
        key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
        cipher_suite = Fernet(key)
        
        # Шифруем данные
        encrypted_data = cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        logger.error(f"Ошибка при шифровании данных: {str(e)}")
        return data

def decrypt_personal_data(encrypted_data: str) -> str:
    """
    Расшифровывает персональные данные
    
    Args:
        encrypted_data: Зашифрованная строка в формате base64
        
    Returns:
        str: Расшифрованная строка
    """
    if not encrypted_data:
        return ""
        
    try:
        # Создаем ключ на основе SECRET_KEY
        key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
        cipher_suite = Fernet(key)
        
        # Расшифровываем данные
        decoded_data = base64.urlsafe_b64decode(encrypted_data)
        decrypted_data = cipher_suite.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"Ошибка при расшифровке данных: {str(e)}")
        return encrypted_data

def mask_phone_number(phone: str, mask_percent: int = 60) -> str:
    """
    Маскирует номер телефона, заменяя часть цифр на '*'
    
    Args:
        phone: Номер телефона
        mask_percent: Процент цифр для маскировки (от 0 до 100)
        
    Returns:
        str: Маскированный номер телефона
    """
    if not phone:
        return ""
        
    # Удаляем все нецифровые символы
    digits = re.sub(r'\D', '', phone)
    
    if not digits:
        return phone
        
    # Определяем количество цифр для маскировки
    total_digits = len(digits)
    mask_count = int(total_digits * mask_percent / 100)
    
    # Оставляем первые и последние цифры открытыми
    visible_count = total_digits - mask_count
    prefix_count = visible_count // 2
    suffix_count = visible_count - prefix_count
    
    # Формируем маскированный номер
    prefix = digits[:prefix_count]
    masked = '*' * mask_count
    suffix = digits[-suffix_count:] if suffix_count > 0 else ''
    
    # Восстанавливаем формат номера
    masked_phone = prefix + masked + suffix
    
    # Если исходный номер содержал форматирование, пытаемся его сохранить
    if re.search(r'\D', phone):
        result = ''
        digit_index = 0
        for char in phone:
            if char.isdigit():
                if digit_index < len(masked_phone):
                    result += masked_phone[digit_index]
                    digit_index += 1
                else:
                    result += '*'
            else:
                result += char
        return result
    
    return masked_phone

def log_security_event(event_type: str, user_id: int, details: Dict[str, Any]) -> None:
    """
    Записывает событие безопасности в журнал
    
    Args:
        event_type: Тип события (login, access_denied, data_encrypted, etc.)
        user_id: ID пользователя
        details: Дополнительные детали события
    """
    event = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'details': details
    }
    
    logger.info(f"Событие безопасности: {json.dumps(event, ensure_ascii=False)}")
    
    # В реальном проекте здесь может быть запись в базу данных или отправка в систему мониторинга

def verify_user_access(user_id: int, required_role: str = None) -> bool:
    """
    Проверяет, имеет ли пользователь доступ к запрашиваемому ресурсу
    
    Args:
        user_id: ID пользователя
        required_role: Требуемая роль (admin, manager, etc.)
        
    Returns:
        bool: True если пользователь имеет доступ, False в противном случае
    """
    # Проверка на администратора
    if required_role == 'admin' and user_id not in ADMIN_IDS:
        log_security_event('access_denied', user_id, {
            'required_role': required_role,
            'reason': 'not_admin'
        })
        return False
        
    # Проверка на блокировку
    if user_id in user_requests and user_requests[user_id].get('blocked_until'):
        if user_requests[user_id]['blocked_until'] > datetime.now():
            log_security_event('access_denied', user_id, {
                'required_role': required_role,
                'reason': 'user_blocked',
                'blocked_until': user_requests[user_id]['blocked_until'].isoformat()
            })
            return False
            
    # Здесь могут быть дополнительные проверки доступа
    
    return True 