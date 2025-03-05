"""
Модуль для шифрования и дешифрования персональных данных.
"""
import base64
import logging
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config import SECRET_KEY

# Создаем ключ шифрования на основе SECRET_KEY
def _get_encryption_key() -> bytes:
    """
    Генерирует ключ шифрования на основе SECRET_KEY.
    
    Returns:
        bytes: Ключ шифрования
    """
    try:
        # Используем PBKDF2 для получения ключа из SECRET_KEY
        salt = b'telegram_bot_salt'  # Соль для PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
        return key
    except Exception as e:
        logging.error(f"Ошибка при генерации ключа шифрования: {e}")
        # Возвращаем случайный ключ в случае ошибки
        return Fernet.generate_key()

# Получаем ключ шифрования
_ENCRYPTION_KEY = _get_encryption_key()
_CIPHER = Fernet(_ENCRYPTION_KEY)

def encrypt_personal_data(data: str) -> str:
    """
    Шифрует персональные данные.
    
    Args:
        data: Данные для шифрования
        
    Returns:
        str: Зашифрованные данные в формате base64
    """
    if not data:
        return ""
    
    try:
        # Шифруем данные
        encrypted_data = _CIPHER.encrypt(data.encode())
        # Кодируем в base64 для хранения в базе данных
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        logging.error(f"Ошибка при шифровании данных: {e}")
        return data

def decrypt_personal_data(encrypted_data: str) -> str:
    """
    Дешифрует персональные данные.
    
    Args:
        encrypted_data: Зашифрованные данные в формате base64
        
    Returns:
        str: Дешифрованные данные
    """
    if not encrypted_data:
        return ""
    
    try:
        # Декодируем из base64
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        # Дешифруем данные
        decrypted_data = _CIPHER.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        logging.error(f"Ошибка при дешифровании данных: {e}")
        return encrypted_data

def mask_phone_number(phone: str, mask_percent: int = 60) -> str:
    """
    Маскирует номер телефона, заменяя часть цифр на '*'.
    
    Args:
        phone: Номер телефона
        mask_percent: Процент цифр для маскировки (от 0 до 100)
        
    Returns:
        str: Маскированный номер телефона
    """
    if not phone:
        return ""
    
    try:
        # Удаляем все нецифровые символы
        digits = ''.join(filter(str.isdigit, phone))
        
        if not digits:
            return phone
        
        # Определяем количество цифр для маскировки
        num_digits = len(digits)
        num_to_mask = int(num_digits * mask_percent / 100)
        
        # Определяем позиции для маскировки (в середине номера)
        start_mask = (num_digits - num_to_mask) // 2
        end_mask = start_mask + num_to_mask
        
        # Создаем маскированный номер
        masked_digits = digits[:start_mask] + '*' * num_to_mask + digits[end_mask:]
        
        # Восстанавливаем формат номера
        masked_phone = phone
        digit_index = 0
        for i, char in enumerate(phone):
            if char.isdigit():
                masked_phone = masked_phone[:i] + masked_digits[digit_index] + masked_phone[i+1:]
                digit_index += 1
        
        return masked_phone
    except Exception as e:
        logging.error(f"Ошибка при маскировке номера телефона: {e}")
        return phone 