"""
Скрипт для тестирования генерации демо-заявок
"""
import random
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Импортируем модели напрямую
from bot.models.models import Base, Category, City, Request, RequestStatus

# Импортируем конфигурацию демо-заявок
from bot.utils.demo_config import DEMO_REQUEST_TEMPLATES, DEMO_CLIENTS

def get_session():
    """Создает и возвращает сессию базы данных"""
    engine = create_engine('sqlite:///bot.db')
    Session = sessionmaker(bind=engine)
    return Session()

def get_active_categories():
    """Получает список активных категорий"""
    session = get_session()
    return session.query(Category).filter(Category.is_active == True).all()

def get_active_cities():
    """Получает список активных городов"""
    session = get_session()
    return session.query(City).filter(City.is_active == True).all()

def generate_demo_client():
    """Генерирует имя и телефон демо-клиента"""
    return random.choice(DEMO_CLIENTS)

def generate_demo_request():
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
                    break
        
        # Если все еще нет шаблонов, создаем общий шаблон
        if not templates:
            templates = ["Требуется консультация специалиста."]
        
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
            "city_id": city.id
        }
        
        logger.info(f"Сгенерирована демо-заявка: {demo_request}")
        
        # Создаем объект заявки
        new_request = Request(
            client_name=client_name,
            client_phone=client_phone,
            description=description,
            status=RequestStatus.NEW,
            is_demo=True,
            category_id=category.id,
            city_id=city.id,
            created_at=datetime.utcnow()
        )
        
        # Сохраняем заявку в базу данных
        session.add(new_request)
        session.commit()
        
        logger.info(f"Демо-заявка сохранена в базу данных с ID: {new_request.id}")
        
        return demo_request
        
    except Exception as e:
        logger.error(f"Ошибка при генерации демо-заявки: {e}")
        if 'session' in locals():
            session.rollback()
        return None

if __name__ == "__main__":
    logger.info("Запуск генерации демо-заявки...")
    demo = generate_demo_request()
    if demo:
        logger.info("Демо-заявка успешно сгенерирована!")
    else:
        logger.error("Не удалось сгенерировать демо-заявку.") 