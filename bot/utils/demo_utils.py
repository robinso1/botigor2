import random
import string
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from config import DEFAULT_CATEGORIES, DEFAULT_CITIES, CITY_PHONE_PREFIXES

logger = logging.getLogger(__name__)

# Список имен для генерации демо-заявок
DEMO_NAMES = [
    "Александр", "Алексей", "Анатолий", "Андрей", "Антон", "Артем", "Борис", "Вадим", "Валентин", "Валерий",
    "Василий", "Виктор", "Виталий", "Владимир", "Владислав", "Геннадий", "Георгий", "Григорий", "Даниил", "Денис",
    "Дмитрий", "Евгений", "Егор", "Иван", "Игорь", "Илья", "Кирилл", "Константин", "Леонид", "Максим",
    "Михаил", "Никита", "Николай", "Олег", "Павел", "Петр", "Роман", "Сергей", "Станислав", "Юрий"
]

# Список фамилий для генерации демо-заявок
DEMO_SURNAMES = [
    "Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", "Соколов", "Михайлов", "Новиков", "Федоров",
    "Морозов", "Волков", "Алексеев", "Лебедев", "Семенов", "Егоров", "Павлов", "Козлов", "Степанов", "Николаев",
    "Орлов", "Андреев", "Макаров", "Никитин", "Захаров", "Зайцев", "Соловьев", "Борисов", "Яковлев", "Григорьев"
]

# Список улиц для генерации демо-заявок
DEMO_STREETS = [
    "Ленина", "Пушкина", "Гагарина", "Мира", "Советская", "Центральная", "Молодежная", "Школьная", "Лесная", "Садовая",
    "Набережная", "Заводская", "Новая", "Октябрьская", "Комсомольская", "Первомайская", "Полевая", "Зеленая", "Луговая", "Солнечная"
]

# Список описаний для генерации демо-заявок
DEMO_DESCRIPTIONS = [
    "Требуется ремонт {area} кв.м. {room_type}. Бюджет ограничен.",
    "Нужен косметический ремонт в {room_type}, площадь {area} кв.м.",
    "Требуется капитальный ремонт {room_type}, площадь {area} кв.м.",
    "Нужно сделать ремонт в {room_type}. Площадь {area} кв.м.",
    "Ищу мастера для ремонта {room_type}. Площадь помещения {area} кв.м.",
    "Требуется {category} в {room_type}. Площадь {area} кв.м.",
    "Нужен специалист по {category} для {room_type}. Площадь {area} кв.м.",
    "Ищу бригаду для {category} в {room_type}. Площадь {area} кв.м.",
    "Требуется {category} под ключ. {room_type}, площадь {area} кв.м.",
    "Нужна помощь с {category} в {room_type}. Площадь {area} кв.м."
]

# Список типов помещений для генерации демо-заявок
DEMO_ROOM_TYPES = [
    "квартиры", "комнаты", "кухни", "ванной", "туалета", "коридора", "спальни", "гостиной", "детской", "балкона",
    "лоджии", "кабинета", "студии", "однокомнатной квартиры", "двухкомнатной квартиры", "трехкомнатной квартиры"
]

def generate_demo_phone(city: str) -> str:
    """
    Генерирует демо-номер телефона с учетом префикса города
    
    Args:
        city (str): Название города
    
    Returns:
        str: Сгенерированный номер телефона с маской
    """
    prefixes = CITY_PHONE_PREFIXES.get(city, ["495", "499", "925", "926"])
    prefix = random.choice(prefixes)
    
    # Генерируем случайные цифры для номера
    digits = ''.join(random.choices(string.digits, k=7))
    
    # Маскируем часть номера
    masked_digits = digits[:3] + "****"
    
    return f"+7 ({prefix}) {masked_digits}"

def generate_demo_address(city: str) -> str:
    """
    Генерирует демо-адрес
    
    Args:
        city (str): Название города
    
    Returns:
        str: Сгенерированный адрес
    """
    street = random.choice(DEMO_STREETS)
    house = random.randint(1, 150)
    apartment = random.randint(1, 300)
    
    return f"г. {city}, ул. {street}, д. {house}, кв. {apartment}"

def generate_demo_request() -> Dict[str, Any]:
    """
    Генерирует демо-заявку
    
    Returns:
        Dict[str, Any]: Словарь с данными демо-заявки
    """
    # Выбираем случайные данные
    category = random.choice(DEFAULT_CATEGORIES)
    city = random.choice(DEFAULT_CITIES)
    first_name = random.choice(DEMO_NAMES)
    last_name = random.choice(DEMO_SURNAMES)
    phone = generate_demo_phone(city)
    address = generate_demo_address(city)
    area = random.randint(10, 150)
    room_type = random.choice(DEMO_ROOM_TYPES)
    
    # Формируем описание
    description_template = random.choice(DEMO_DESCRIPTIONS)
    description = description_template.format(
        category=category.lower(),
        room_type=room_type,
        area=area
    )
    
    # Создаем заявку
    return {
        "client_name": f"{first_name} {last_name}",
        "client_phone": phone,
        "description": description,
        "category": category,
        "city": city,
        "area": area,
        "address": address,
        "is_demo": True,
        "created_at": datetime.utcnow()
    }

def should_generate_demo_request() -> bool:
    """
    Определяет, нужно ли генерировать демо-заявку в данный момент
    
    Returns:
        bool: True, если нужно генерировать демо-заявку, иначе False
    """
    # Простая логика: генерируем с вероятностью 10%
    return random.random() < 0.1 