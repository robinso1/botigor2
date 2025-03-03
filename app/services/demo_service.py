from sqlalchemy.orm import Session
from app.models import Request, Category, City, RequestStatus
from app.config import settings
import random
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DemoService:
    def __init__(self, db: Session):
        self.db = db
        
        # Примеры имен и описаний для демо-заявок
        self.demo_names = [
            "Александр", "Елена", "Михаил", "Анна", "Дмитрий",
            "Ольга", "Сергей", "Наталья", "Андрей", "Мария"
        ]
        
        self.demo_descriptions = [
            "Нужен ремонт квартиры под ключ",
            "Требуется косметический ремонт",
            "Ремонт ванной комнаты",
            "Отделка новой квартиры",
            "Требуется укладка плитки",
            "Нужно поклеить обои",
            "Ремонт кухни под ключ",
            "Требуется шпаклевка стен",
            "Установка натяжных потолков",
            "Требуется электрик для проводки"
        ]
        
        self.demo_areas = [
            "45 м²", "60 м²", "75 м²", "90 м²", "120 м²",
            "150 м²", "180 м²", "200 м²", "250 м²", "300 м²"
        ]
    
    def generate_phone_number(self, city: City) -> str:
        """Генерация демо номера телефона"""
        prefix = city.phone_prefix or "495"  # По умолчанию используем московский код
        # Генерируем случайный номер и маскируем часть цифр
        number = ''.join([str(random.randint(0, 9)) for _ in range(7)])
        masked_number = f"+7 ({prefix}) {number[:2]}**-**-{number[5:]}"
        return masked_number
    
    def create_demo_request(self) -> Request:
        """Создание одной демо-заявки"""
        # Получаем случайную категорию и город
        categories = self.db.query(Category).all()
        cities = self.db.query(City).all()
        
        if not categories or not cities:
            logger.error("No categories or cities found in database")
            return None
        
        category = random.choice(categories)
        city = random.choice(cities)
        
        # Создаем демо-заявку
        request = Request(
            client_name=random.choice(self.demo_names),
            client_phone=self.generate_phone_number(city),
            description=random.choice(self.demo_descriptions),
            area=random.choice(self.demo_areas),
            category_id=category.id,
            city_id=city.id,
            is_demo=True,
            status=RequestStatus.NEW
        )
        
        self.db.add(request)
        self.db.commit()
        
        logger.info(f"Created demo request: {request.id}")
        return request
    
    def generate_daily_requests(self) -> list[Request]:
        """Генерация демо-заявок на день"""
        if not settings.DEMO_MODE:
            return []
        
        # Проверяем, сколько демо-заявок уже создано сегодня
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_requests = self.db.query(Request).filter(
            Request.is_demo == True,
            Request.created_at >= today_start
        ).count()
        
        # Если уже достигнут лимит на сегодня, не создаем новые
        if today_requests >= settings.DEMO_REQUESTS_PER_DAY:
            return []
        
        # Создаем случайное количество заявок
        num_requests = random.randint(1, settings.DEMO_REQUESTS_PER_DAY - today_requests)
        requests = []
        
        for _ in range(num_requests):
            request = self.create_demo_request()
            if request:
                requests.append(request)
        
        return requests 