import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from bot.models import Request, User, Category, City, Distribution
from config import DEFAULT_DISTRIBUTION_INTERVAL, DEFAULT_USERS_PER_REQUEST, DEFAULT_MAX_DISTRIBUTIONS, RESERVE_USERS_PER_REQUEST, DEMO_PHONE_MASK_PERCENT
from bot.utils.security_utils import encrypt_personal_data, mask_phone_number, log_security_event
from bot.utils.crm_utils import send_to_crm

logger = logging.getLogger(__name__)

class RequestService:
    """Сервис для работы с заявками"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_request(self, data: Dict[str, Any]) -> Request:
        """
        Создает новую заявку
        
        Args:
            data (Dict[str, Any]): Данные заявки
        
        Returns:
            Request: Созданная заявка
        """
        # Получаем категорию и город, если они указаны
        category = None
        city = None
        
        if "category" in data:
            category = self.session.query(Category).filter(Category.name == data["category"]).first()
            if not category:
                logger.warning(f"Категория '{data['category']}' не найдена")
        
        if "city" in data:
            city = self.session.query(City).filter(City.name == data["city"]).first()
            if not city:
                logger.warning(f"Город '{data['city']}' не найден")
        
        # Шифруем персональные данные
        client_name = data.get("client_name")
        client_phone = data.get("client_phone")
        
        if not data.get("is_demo"):
            # Для реальных заявок шифруем данные
            encrypted_name = encrypt_personal_data(client_name) if client_name else None
            encrypted_phone = encrypt_personal_data(client_phone) if client_phone else None
        else:
            # Для демо-заявок маскируем телефон
            encrypted_name = client_name
            encrypted_phone = mask_phone_number(client_phone, DEMO_PHONE_MASK_PERCENT) if client_phone else None
        
        # Создаем заявку
        request = Request(
            source_chat_id=data.get("source_chat_id"),
            source_message_id=data.get("source_message_id"),
            client_name=encrypted_name,
            client_phone=encrypted_phone,
            description=data.get("description"),
            status=data.get("status", "новая"),
            area=data.get("area"),
            address=data.get("address"),
            is_demo=data.get("is_demo", False),
            category_id=category.id if category else None,
            city_id=city.id if city else None,
            extra_data=data.get("extra_data")
        )
        
        self.session.add(request)
        self.session.commit()
        
        # Логируем создание заявки
        log_security_event(
            "request_created",
            data.get("created_by", 0),
            {
                "request_id": request.id,
                "is_demo": request.is_demo,
                "category": category.name if category else None,
                "city": city.name if city else None
            }
        )
        
        # Отправляем данные в CRM
        if not request.is_demo:
            crm_data = {
                "id": request.id,
                "client_name": client_name,  # Отправляем незашифрованные данные
                "client_phone": client_phone,
                "description": request.description,
                "category_id": request.category_id,
                "address": request.address,
                "area": request.area
            }
            send_to_crm(crm_data)
        
        logger.info(f"Создана новая заявка: ID={request.id}, клиент={request.client_name}")
        return request
    
    def update_request(self, request_id: int, data: Dict[str, Any]) -> Optional[Request]:
        """
        Обновляет существующую заявку
        
        Args:
            request_id (int): ID заявки
            data (Dict[str, Any]): Новые данные заявки
        
        Returns:
            Optional[Request]: Обновленная заявка или None, если заявка не найдена
        """
        request = self.session.query(Request).filter(Request.id == request_id).first()
        if not request:
            logger.warning(f"Заявка с ID={request_id} не найдена")
            return None
        
        # Обновляем категорию, если она указана
        if "category" in data:
            category = self.session.query(Category).filter(Category.name == data["category"]).first()
            if category:
                request.category_id = category.id
            else:
                logger.warning(f"Категория '{data['category']}' не найдена")
        
        # Обновляем город, если он указан
        if "city" in data:
            city = self.session.query(City).filter(City.name == data["city"]).first()
            if city:
                request.city_id = city.id
            else:
                logger.warning(f"Город '{data['city']}' не найден")
        
        # Обновляем остальные поля
        for key, value in data.items():
            if key not in ["category", "city"] and hasattr(request, key):
                setattr(request, key, value)
        
        request.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.info(f"Обновлена заявка: ID={request.id}, статус={request.status}")
        return request
    
    def get_request_by_id(self, request_id: int) -> Optional[Request]:
        """
        Получает заявку по ID
        
        Args:
            request_id (int): ID заявки
        
        Returns:
            Optional[Request]: Заявка или None, если заявка не найдена
        """
        return self.session.query(Request).filter(Request.id == request_id).first()
    
    def get_requests_for_distribution(self) -> List[Request]:
        """
        Получает список заявок, которые нужно распределить
        
        Returns:
            List[Request]: Список заявок для распределения
        """
        # Получаем заявки со статусом "новая" или "актуальная"
        return self.session.query(Request).filter(
            Request.status.in_(["новая", "актуальная"])
        ).all()
    
    def distribute_request(self, request_id: int) -> List[Distribution]:
        """
        Распределяет заявку между пользователями
        
        Args:
            request_id (int): ID заявки
        
        Returns:
            List[Distribution]: Список созданных распределений
        """
        request = self.get_request_by_id(request_id)
        if not request:
            logger.warning(f"Заявка с ID={request_id} не найдена")
            return []
        
        # Проверяем, сколько раз заявка уже была распределена
        distribution_count = self.session.query(func.count(Distribution.id)).filter(
            Distribution.request_id == request_id
        ).scalar()
        
        if distribution_count >= DEFAULT_MAX_DISTRIBUTIONS:
            logger.info(f"Заявка с ID={request_id} уже была распределена максимальное количество раз")
            return []
        
        # Получаем пользователей для распределения
        users = self._get_users_for_request(request)
        
        # Создаем распределения
        distributions = []
        for user in users:
            distribution = Distribution(
                request_id=request.id,
                user_id=user.id,
                status="отправлено",
                created_at=datetime.utcnow()
            )
            self.session.add(distribution)
            distributions.append(distribution)
        
        # Обновляем статус заявки
        if distributions:
            request.status = "актуальная"
        
        self.session.commit()
        
        logger.info(f"Заявка с ID={request_id} распределена {len(distributions)} пользователям")
        return distributions
    
    def _get_users_for_request(self, request: Request) -> List[User]:
        """
        Получает список пользователей, которым можно отправить заявку
        
        Args:
            request (Request): Заявка
        
        Returns:
            List[User]: Список пользователей
        """
        query = self.session.query(User).filter(User.is_active == True)
        
        # Фильтруем по категории, если она указана
        if request.category_id:
            query = query.join(User.categories).filter(Category.id == request.category_id)
        
        # Фильтруем по городу, если он указан
        if request.city_id:
            query = query.join(User.cities).filter(City.id == request.city_id)
        
        # Получаем пользователей, которым еще не отправляли эту заявку
        already_distributed_user_ids = self.session.query(Distribution.user_id).filter(
            Distribution.request_id == request.id
        ).all()
        already_distributed_user_ids = [user_id for (user_id,) in already_distributed_user_ids]
        
        if already_distributed_user_ids:
            query = query.filter(User.id.notin_(already_distributed_user_ids))
        
        # Получаем пользователей, которым не отправляли заявки в течение интервала
        interval_time = datetime.utcnow() - timedelta(hours=DEFAULT_DISTRIBUTION_INTERVAL)
        recently_distributed_user_ids = self.session.query(Distribution.user_id).filter(
            Distribution.created_at >= interval_time
        ).all()
        recently_distributed_user_ids = [user_id for (user_id,) in recently_distributed_user_ids]
        
        if recently_distributed_user_ids:
            query = query.filter(User.id.notin_(recently_distributed_user_ids))
        
        # Получаем всех подходящих пользователей
        users = query.all()
        
        # Если пользователей достаточно, разделяем на основной и резервный потоки
        if len(users) > DEFAULT_USERS_PER_REQUEST:
            main_users = users[:DEFAULT_USERS_PER_REQUEST]
            reserve_users = users[DEFAULT_USERS_PER_REQUEST:DEFAULT_USERS_PER_REQUEST + RESERVE_USERS_PER_REQUEST]
            # Чередуем прямой и обратный порядок
            if request.id % 2 == 0:
                return main_users + reserve_users
            else:
                return list(reversed(main_users + reserve_users))
        
        return users
    
    def get_request_statistics(self) -> Dict[str, Any]:
        """
        Получает статистику по заявкам
        
        Returns:
            Dict[str, Any]: Статистика по заявкам
        """
        total_requests = self.session.query(func.count(Request.id)).scalar()
        
        # Статистика по статусам
        status_stats = {}
        for status in ["новая", "актуальная", "неактуальная", "в работе", "замер", "отказ клиента", "выполнена"]:
            count = self.session.query(func.count(Request.id)).filter(Request.status == status).scalar()
            status_stats[status] = count
        
        # Статистика по категориям
        category_stats = {}
        categories = self.session.query(Category).all()
        for category in categories:
            count = self.session.query(func.count(Request.id)).filter(Request.category_id == category.id).scalar()
            category_stats[category.name] = count
        
        # Статистика по городам
        city_stats = {}
        cities = self.session.query(City).all()
        for city in cities:
            count = self.session.query(func.count(Request.id)).filter(Request.city_id == city.id).scalar()
            city_stats[city.name] = count
        
        # Статистика по распределениям
        total_distributions = self.session.query(func.count(Distribution.id)).scalar()
        
        return {
            "total_requests": total_requests,
            "status_stats": status_stats,
            "category_stats": category_stats,
            "city_stats": city_stats,
            "total_distributions": total_distributions
        }
    
    def get_user_distributions(self, telegram_id: int) -> List[Distribution]:
        """
        Получает список распределений для пользователя
        
        Args:
            telegram_id (int): Telegram ID пользователя
        
        Returns:
            List[Distribution]: Список распределений
        """
        # Получаем пользователя по Telegram ID
        user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            logger.warning(f"Пользователь с Telegram ID={telegram_id} не найден")
            return []
        
        # Получаем распределения пользователя
        distributions = self.session.query(Distribution).filter(
            Distribution.user_id == user.id
        ).order_by(Distribution.created_at.desc()).all()
        
        return distributions
    
    def get_distribution(self, distribution_id: int) -> Optional[Distribution]:
        """
        Получает распределение по ID
        
        Args:
            distribution_id (int): ID распределения
        
        Returns:
            Optional[Distribution]: Распределение или None, если распределение не найдено
        """
        return self.session.query(Distribution).filter(Distribution.id == distribution_id).first()
    
    def update_distribution_status(self, distribution_id: int, status: str) -> Optional[Distribution]:
        """
        Обновляет статус распределения
        
        Args:
            distribution_id (int): ID распределения
            status (str): Новый статус
        
        Returns:
            Optional[Distribution]: Обновленное распределение или None, если распределение не найдено
        """
        distribution = self.get_distribution(distribution_id)
        if not distribution:
            logger.warning(f"Распределение с ID={distribution_id} не найдено")
            return None
        
        distribution.status = status
        distribution.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.info(f"Обновлен статус распределения: ID={distribution.id}, статус={status}")
        return distribution 