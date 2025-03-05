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
    DEMO_DISTRIBUTION_SETTINGS
)

logger = logging.getLogger(__name__)

def generate_demo_phone(city: str) -> str:
    """Генерирует демо-телефон для указанного города"""
    return random.choice(DEMO_CLIENTS)[1]

def generate_demo_client() -> Tuple[str, str]:
    """Генерирует имя и телефон демо-клиента"""
    return random.choice(DEMO_CLIENTS)

def should_generate_demo_request() -> bool:
    """Определяет, нужно ли генерировать демо-заявку в данный момент"""
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
    """Получает список активных категорий"""
    session = get_session()
    try:
        categories = session.query(Category).filter(Category.is_active == True).all()
        logger.debug(f"Найдено {len(categories)} активных категорий")
        return categories
    finally:
        session.close()

def get_active_cities() -> List[City]:
    """Получает список активных городов"""
    session = get_session()
    try:
        cities = session.query(City).filter(City.is_active == True).all()
        logger.debug(f"Найдено {len(cities)} активных городов")
        return cities
    finally:
        session.close()

def generate_demo_request() -> Optional[Dict[str, Any]]:
    """Генерирует демо-заявку"""
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
        client_name, client_phone = generate_demo_client()
        
        # Создаем демо-заявку
        demo_request = {
            "client_name": client_name,
            "client_phone": client_phone,
            "description": description,
            "status": RequestStatus.NEW,
            "is_demo": True,
            "category_id": category.id,
            "city_id": city.id,
            "created_at": datetime.utcnow()
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
    """Удаляет старые демо-заявки"""
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