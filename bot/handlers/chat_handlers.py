import logging
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from telegram import Update
from telegram.ext import ContextTypes

from bot.models import get_session
from bot.services.request_service import RequestService
from config import MONITORED_CHATS

logger = logging.getLogger(__name__)

async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает сообщения из чатов и извлекает из них заявки
    """
    # Проверяем, что сообщение пришло из мониторируемого чата
    if update.effective_chat.id not in MONITORED_CHATS:
        return
    
    # Получаем текст сообщения
    message_text = update.effective_message.text or update.effective_message.caption or ""
    
    # Пытаемся извлечь данные заявки из сообщения
    request_data = extract_request_data(message_text)
    
    if not request_data:
        logger.info(f"Не удалось извлечь данные заявки из сообщения в чате {update.effective_chat.id}")
        return
    
    # Добавляем информацию о чате и сообщении
    request_data["source_chat_id"] = update.effective_chat.id
    request_data["source_message_id"] = update.effective_message.message_id
    
    # Создаем заявку
    session = get_session()
    request_service = RequestService(session)
    request = request_service.create_request(request_data)
    
    logger.info(f"Создана новая заявка из чата {update.effective_chat.id}: ID={request.id}")
    
    # Распределяем заявку
    distributions = request_service.distribute_request(request.id)
    
    logger.info(f"Заявка ID={request.id} распределена {len(distributions)} пользователям")

def extract_request_data(text: str) -> Optional[Dict[str, Any]]:
    """
    Извлекает данные заявки из текста сообщения
    
    Args:
        text (str): Текст сообщения
    
    Returns:
        Optional[Dict[str, Any]]: Данные заявки или None, если не удалось извлечь
    """
    # Пример простого извлечения данных
    # В реальном проекте здесь будет более сложная логика
    
    # Извлекаем имя клиента
    name_match = re.search(r"(?:имя|клиент|заказчик)[:\s]+([^\n]+)", text, re.IGNORECASE)
    client_name = name_match.group(1).strip() if name_match else None
    
    # Извлекаем телефон
    phone_match = re.search(r"(?:телефон|тел|номер)[:\s]+([^\n]+)", text, re.IGNORECASE)
    client_phone = phone_match.group(1).strip() if phone_match else None
    
    # Извлекаем категорию
    category_match = re.search(r"(?:категория|вид работ|работы)[:\s]+([^\n]+)", text, re.IGNORECASE)
    category = category_match.group(1).strip() if category_match else None
    
    # Извлекаем город
    city_match = re.search(r"(?:город|местоположение|адрес)[:\s]+([^\n]+)", text, re.IGNORECASE)
    city = city_match.group(1).strip() if city_match else None
    
    # Извлекаем площадь
    area_match = re.search(r"(?:площадь|кв\.м)[:\s]+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    area = float(area_match.group(1)) if area_match else None
    
    # Извлекаем описание
    description_match = re.search(r"(?:описание|детали|задача)[:\s]+([^\n]+)", text, re.IGNORECASE)
    description = description_match.group(1).strip() if description_match else text
    
    # Если не удалось извлечь ключевые данные, возвращаем None
    if not (client_name or client_phone or description):
        return None
    
    return {
        "client_name": client_name,
        "client_phone": client_phone,
        "category": category,
        "city": city,
        "area": area,
        "description": description,
        "status": "новая"
    } 