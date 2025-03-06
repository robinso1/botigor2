"""
Модуль для генерации демо-заявок
"""
import logging
import random
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import json

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from bot.models import get_session, Category, City, Request, RequestStatus
from bot.utils.demo_config import (
    DEMO_REQUEST_TEMPLATES, 
    DEMO_CLIENTS, 
    DEMO_GENERATION_INTERVALS,
    DEMO_DISTRIBUTION_SETTINGS,
    DEMO_INFO_MESSAGES
)
from bot.utils.encryption import mask_phone_number

logger = logging.getLogger(__name__)

def generate_demo_phone(city: str = None) -> str:
    """
    Генерирует демо-телефон для указанного города
    
    Args:
        city: Название города
        
    Returns:
        str: Сгенерированный телефон
    """
    # Выбираем телефон с нужным префиксом в зависимости от города
    if city:
        if "Москва" in city:
            phones = [phone for name, phone in DEMO_CLIENTS if phone.startswith("+7495") or phone.startswith("+7499")]
        elif "Санкт-Петербург" in city or "Петербург" in city:
            phones = [phone for name, phone in DEMO_CLIENTS if phone.startswith("+7812")]
        else:
            phones = [phone for name, phone in DEMO_CLIENTS]
    else:
        phones = [phone for name, phone in DEMO_CLIENTS]
    
    if not phones:
        return random.choice(DEMO_CLIENTS)[1]
    
    return random.choice(phones)

def generate_demo_client(city: str = None) -> Tuple[str, str]:
    """
    Генерирует имя и телефон демо-клиента
    
    Args:
        city: Название города
        
    Returns:
        Tuple[str, str]: Имя и телефон клиента
    """
    name = random.choice(DEMO_CLIENTS)[0]
    phone = generate_demo_phone(city)
    return (name, phone)

def should_generate_demo_request() -> bool:
    """
    Определяет, нужно ли генерировать демо-заявку в данный момент
    
    Returns:
        bool: True, если нужно генерировать заявку, иначе False
    """
    try:
        session = get_session()
        
        # Получаем время последней демо-заявки
        last_demo = session.query(Request).filter(
            Request.is_demo == True
        ).order_by(Request.created_at.desc()).first()
        
        if not last_demo:
            logger.info("Не найдено предыдущих демо-заявок, генерируем новую")
            return True
        
        # Определяем случайный интервал для следующей заявки
        interval_seconds = random.randint(
            DEMO_GENERATION_INTERVALS["min"],
            DEMO_GENERATION_INTERVALS["max"]
        )
        
        # Проверяем, прошло ли достаточно времени с момента последней заявки
        next_time = last_demo.created_at + timedelta(seconds=interval_seconds)
        current_time = datetime.utcnow()
        
        should_generate = current_time > next_time
        
        if should_generate:
            logger.info(f"Прошло достаточно времени с момента последней демо-заявки ({last_demo.created_at}), генерируем новую")
        else:
            time_left = (next_time - current_time).total_seconds()
            logger.debug(f"Еще не время для генерации новой демо-заявки, осталось {time_left:.0f} секунд")
            
        return should_generate
        
    except Exception as e:
        logger.error(f"Ошибка при проверке необходимости генерации демо-заявки: {e}")
        return False
    finally:
        if 'session' in locals():
            session.close()

def get_active_categories() -> List[Category]:
    """
    Получает список активных категорий
    
    Returns:
        List[Category]: Список активных категорий
    """
    session = get_session()
    try:
        categories = session.query(Category).filter(Category.is_active == True).all()
        logger.debug(f"Найдено {len(categories)} активных категорий")
        return categories
    finally:
        session.close()

def get_active_cities() -> List[City]:
    """
    Получает список активных городов
    
    Returns:
        List[City]: Список активных городов
    """
    session = get_session()
    try:
        cities = session.query(City).filter(City.is_active == True).all()
        logger.debug(f"Найдено {len(cities)} активных городов")
        return cities
    finally:
        session.close()

def generate_demo_request() -> Optional[Dict[str, Any]]:
    """
    Генерирует демо-заявку
    
    Returns:
        Optional[Dict[str, Any]]: Данные демо-заявки или None в случае ошибки
    """
    try:
        session = get_session()
        
        # Получаем активные категории и города
        categories = get_active_categories()
        cities = get_active_cities()
        
        if not categories:
            logger.warning("Нет активных категорий для генерации демо-заявки")
            return None
            
        if not cities:
            logger.warning("Нет активных городов для генерации демо-заявки")
            return None
        
        # Выбираем случайную категорию и город
        category = random.choice(categories)
        city = random.choice(cities)
        
        logger.info(f"Выбрана категория: {category.name}, город: {city.name}")
        
        # Получаем шаблоны для выбранной категории
        templates = DEMO_REQUEST_TEMPLATES.get(category.name, [])
        if not templates:
            logger.warning(f"Нет шаблонов для категории {category.name}")
            # Используем шаблоны из первой доступной категории
            for cat_name, cat_templates in DEMO_REQUEST_TEMPLATES.items():
                if cat_templates:
                    templates = cat_templates
                    logger.info(f"Используем шаблоны из категории {cat_name}")
                    break
        
        # Если все еще нет шаблонов, создаем общий шаблон
        if not templates:
            templates = ["Требуется консультация специалиста."]
            logger.info("Используем общий шаблон для заявки")
        
        # Выбираем случайный шаблон
        description = random.choice(templates)
        
        # Генерируем данные клиента
        client_name, client_phone = generate_demo_client(city.name)
        
        # Генерируем случайную площадь помещения (от 20 до 200 м²)
        area = round(random.uniform(20, 200), 2)
        
        # Генерируем случайную стоимость (от 5000 до 100000 руб.)
        estimated_cost = round(random.uniform(5000, 100000), 2)
        
        # Генерируем случайный адрес
        streets = ["Ленина", "Пушкина", "Гагарина", "Мира", "Советская", "Центральная", "Молодежная", "Школьная", "Лесная", "Садовая"]
        street = random.choice(streets)
        house = random.randint(1, 150)
        apartment = random.randint(1, 300)
        address = f"ул. {street}, д. {house}, кв. {apartment}"
        
        # Маскируем телефон
        masked_phone = mask_phone_number(client_phone, DEMO_DISTRIBUTION_SETTINGS["mask_phone_percent"])
        
        # Создаем демо-заявку
        demo_request = {
            "client_name": client_name,
            "client_phone": masked_phone,
            "description": description,
            "status": RequestStatus.NEW,
            "is_demo": True,
            "category_id": category.id,
            "city_id": city.id,
            "area": area,
            "address": address,
            "estimated_cost": estimated_cost,
            "created_at": datetime.utcnow(),
            "extra_data": {
                "demo_info": "Это демо-заявка для тестирования системы",
                "original_phone": client_phone,
                "category_name": category.name,
                "city_name": city.name,
                "demo_message": get_demo_info_message("after_request")
            }
        }
        
        logger.info(f"Сгенерирована демо-заявка: {demo_request}")
        return demo_request
        
    except Exception as e:
        logger.error(f"Ошибка при генерации демо-заявки: {e}")
        return None
    finally:
        if 'session' in locals():
            session.close()

def cleanup_old_demo_requests():
    """
    Удаляет старые демо-заявки
    """
    try:
        session = get_session()
        expiration_hours = DEMO_DISTRIBUTION_SETTINGS.get("expiration_hours", 24)
        expiration_time = datetime.utcnow() - timedelta(hours=expiration_hours)
        
        # Находим старые демо-заявки
        old_demos = session.query(Request).filter(
            and_(
                Request.is_demo == True,
                Request.created_at < expiration_time
            )
        ).all()
        
        if not old_demos:
            logger.debug("Нет старых демо-заявок для удаления")
            return
            
        # Удаляем найденные заявки
        for demo in old_demos:
            session.delete(demo)
        
        session.commit()
        logger.info(f"Удалено {len(old_demos)} старых демо-заявок")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке старых демо-заявок: {e}")
        if 'session' in locals():
            session.rollback()
    finally:
        if 'session' in locals():
            session.close()

def get_demo_info_message(message_type: str = "after_request") -> str:
    """
    Возвращает информационное сообщение для демо-режима
    
    Args:
        message_type: Тип сообщения (after_request, instructions, conditions, testimonials, tips)
        
    Returns:
        str: Информационное сообщение
    """
    if message_type == "after_request":
        return DEMO_INFO_MESSAGES["after_request"]
    
    if message_type == "instructions":
        return random.choice(DEMO_INFO_MESSAGES["instructions"])
    
    if message_type == "conditions":
        return random.choice(DEMO_INFO_MESSAGES["conditions"])
    
    if message_type == "testimonials":
        return random.choice(DEMO_INFO_MESSAGES["testimonials"])
    
    if message_type == "tips":
        return random.choice(DEMO_INFO_MESSAGES["tips"])
    
    # Если тип сообщения не указан или неверный, возвращаем случайное сообщение
    message_types = ["instructions", "conditions", "testimonials", "tips"]
    return get_demo_info_message(random.choice(message_types))

def schedule_demo_info_message() -> str:
    """
    Возвращает случайное информационное сообщение для периодической отправки
    
    Returns:
        str: Информационное сообщение
    """
    message_types = ["instructions", "conditions", "testimonials", "tips"]
    return get_demo_info_message(random.choice(message_types)) 