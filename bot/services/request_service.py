"""
Модуль для работы с заявками.
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from bot.models import Request, User, Category, City, Distribution, RequestStatus, DistributionStatus, SubCategory
from bot.utils import (
    encrypt_personal_data, 
    decrypt_personal_data,
    mask_phone_number, 
    log_security_event, 
    send_to_crm
)
from config import (
    DEFAULT_DISTRIBUTION_INTERVAL, 
    DEFAULT_USERS_PER_REQUEST, 
    RESERVE_USERS_PER_REQUEST,
    DEFAULT_MAX_DISTRIBUTIONS,
    DEMO_MODE,
    DEMO_PHONE_MASK_PERCENT
)
from bot.services.crm_service import send_request_to_crm

logger = logging.getLogger(__name__)

class RequestService:
    """Сервис для работы с заявками"""
    
    def __init__(self, session: Session):
        self.session = session
        
    async def create_request(self, data: Dict[str, Any]) -> Optional[Request]:
        """
        Создает новую заявку
        
        Args:
            data: Данные заявки
            
        Returns:
            Optional[Request]: Созданная заявка или None в случае ошибки
        """
        try:
            # Получаем категорию и город
            category = None
            if 'category_id' in data and data['category_id']:
                category = self.session.query(Category).filter_by(id=data['category_id']).first()
            elif 'category_name' in data and data['category_name']:
                category = self.session.query(Category).filter_by(name=data['category_name']).first()
            
            city = None
            if 'city_id' in data and data['city_id']:
                city = self.session.query(City).filter_by(id=data['city_id']).first()
            elif 'city_name' in data and data['city_name']:
                city = self.session.query(City).filter_by(name=data['city_name']).first()
            
            if not category:
                logger.warning(f"Категория с ID {data['category_id']} не найдена")
                return None
            
            if not city:
                logger.warning(f"Город с ID {data['city_id']} не найден")
                return None
            
            # Шифруем персональные данные
            if data.get('client_name'):
                data['client_name'] = encrypt_personal_data(data['client_name'])
                
            if data.get('client_phone'):
                data['client_phone'] = encrypt_personal_data(data['client_phone'])
                
            if data.get('address'):
                data['address'] = encrypt_personal_data(data['address'])
                
            # Логируем событие безопасности
            log_security_event('data_encrypted', 0, {
                'request_id': data.get('id'),
                'fields': ['client_name', 'client_phone', 'address']
            })
            
            # Создаем заявку
            request = Request(
                source_chat_id=data.get('source_chat_id'),
                source_message_id=data.get('source_message_id'),
                client_name=data.get('client_name'),
                client_phone=data.get('client_phone'),
                description=data.get('description'),
                status=data.get('status', RequestStatus.NEW),
                area=data.get('area'),
                address=data.get('address'),
                is_demo=data.get('is_demo', False),
                category=category,
                city=city,
                extra_data=data.get('extra_data'),
                estimated_cost=data.get('estimated_cost'),
                # Добавляем новые поля для подкатегорий
                area_value=data.get('area_value'),
                house_type=data.get('house_type'),
                has_design_project=data.get('has_design_project', False)
            )
            
            # Добавляем подкатегории, если они указаны
            if 'subcategory_ids' in data and data['subcategory_ids']:
                subcategories = self.session.query(SubCategory).filter(
                    SubCategory.id.in_(data['subcategory_ids'])
                ).all()
                request.subcategories.extend(subcategories)
            
            # Добавляем заявку в базу данных
            self.session.add(request)
            self.session.commit()
            
            # Отправляем заявку в CRM
            asyncio.create_task(send_request_to_crm(request))
            
            logger.info(f"Создана новая заявка #{request.id} от {data.get('client_name')}")
            return request
        except Exception as e:
            logger.error(f"Ошибка при создании заявки: {e}")
            self.session.rollback()
            return None
        
    async def update_request(self, request_id: int, data: Dict[str, Any]) -> Optional[Request]:
        """
        Обновляет существующую заявку
        
        Args:
            request_id: ID заявки
            data: Новые данные
            
        Returns:
            Optional[Request]: Обновленная заявка или None, если заявка не найдена
        """
        try:
            request = await self.get_request(request_id)
            if not request:
                logger.warning(f"Заявка #{request_id} не найдена")
                return None
            
            # Обновляем категорию
            if 'category_id' in data and data['category_id']:
                category = self.session.query(Category).filter_by(id=data['category_id']).first()
                if category:
                    request.category = category
            
            # Обновляем город
            if 'city_id' in data and data['city_id']:
                city = self.session.query(City).filter_by(id=data['city_id']).first()
                if city:
                    request.city = city
            
            # Обновляем статус
            if 'status' in data:
                try:
                    request.status = RequestStatus(data['status'])
                except ValueError:
                    logger.warning(f"Неверный статус: {data['status']}")
            
            # Обновляем остальные поля
            for field in ['client_name', 'client_phone', 'description', 'area', 'address', 'estimated_cost', 'crm_id', 'crm_status']:
                if field in data:
                    # Шифруем персональные данные
                    if field in ['client_name', 'client_phone', 'address'] and not request.is_demo:
                        setattr(request, field, encrypt_personal_data(data[field]))
                    else:
                        setattr(request, field, data[field])
            
            # Обновляем поля подкатегорий
            for field in ['area_value', 'house_type', 'has_design_project']:
                if field in data:
                    setattr(request, field, data[field])
            
            # Обновляем подкатегории
            if 'subcategory_ids' in data:
                # Очищаем текущие подкатегории
                request.subcategories = []
                
                # Добавляем новые подкатегории
                if data['subcategory_ids']:
                    subcategories = self.session.query(SubCategory).filter(
                        SubCategory.id.in_(data['subcategory_ids'])
                    ).all()
                    request.subcategories.extend(subcategories)
            
            # Обновляем дополнительные данные
            if 'extra_data' in data:
                if request.extra_data:
                    request.extra_data.update(data['extra_data'])
                else:
                    request.extra_data = data['extra_data']
            
            request.updated_at = datetime.utcnow()
            await self.session.commit()
            
            logger.info(f"Заявка #{request_id} обновлена")
            return request
        except Exception as e:
            logger.error(f"Ошибка при обновлении заявки #{request_id}: {e}")
            await self.session.rollback()
            return None
        
    async def get_request(self, request_id: int) -> Optional[Request]:
        """
        Получает заявку по ID
        
        Args:
            request_id: ID заявки
            
        Returns:
            Optional[Request]: Заявка или None, если заявка не найдена
        """
        try:
            result = await self.session.execute(
                select(Request).where(Request.id == request_id)
            )
            request = result.scalar_one_or_none()
            
            return request
        except Exception as e:
            logger.error(f"Ошибка при получении заявки #{request_id}: {e}")
            return None
        
    def get_requests_for_distribution(self) -> List[Request]:
        """
        Получает список заявок для распределения
        
        Returns:
            List[Request]: Список заявок
        """
        # Получаем заявки со статусом "новая" или "актуальная"
        requests = self.session.query(Request).filter(
            Request.status.in_([RequestStatus.NEW, RequestStatus.ACTUAL])
        ).all()
        
        # Фильтруем заявки, которые уже были распределены максимальное количество раз
        result = []
        for request in requests:
            distributions_count = self.session.query(func.count(Distribution.id)).filter_by(request_id=request.id).scalar()
            if distributions_count < DEFAULT_MAX_DISTRIBUTIONS:
                result.append(request)
                
        return result
        
    def distribute_request(self, request_id: int) -> List[Distribution]:
        """
        Распределяет заявку между пользователями
        
        Args:
            request_id: ID заявки
            
        Returns:
            List[Distribution]: Список созданных распределений
        """
        request = self.session.query(Request).filter_by(id=request_id).first()
        if not request:
            logger.warning(f"Заявка #{request_id} не найдена")
            return []
            
        # Проверяем, не превышено ли максимальное количество распределений
        distributions_count = self.session.query(func.count(Distribution.id)).filter_by(request_id=request_id).scalar()
        if distributions_count >= DEFAULT_MAX_DISTRIBUTIONS:
            logger.info(f"Заявка #{request_id} уже была распределена максимальное количество раз")
            return []
            
        # Проверяем, прошло ли достаточно времени с последнего распределения
        last_distribution = self.session.query(Distribution).filter_by(request_id=request_id).order_by(desc(Distribution.created_at)).first()
        if last_distribution:
            time_since_last = datetime.utcnow() - last_distribution.created_at
            if time_since_last < timedelta(hours=DEFAULT_DISTRIBUTION_INTERVAL):
                logger.info(f"С момента последнего распределения заявки #{request_id} прошло недостаточно времени")
                return []
                
        # Получаем подходящих пользователей
        users = self._get_users_for_request(request)
        if not users:
            logger.warning(f"Не найдено подходящих пользователей для заявки #{request_id}")
            return []
            
        # Определяем порядок распределения
        if distributions_count % 2 == 0:
            # Прямой порядок
            selected_users = users[:DEFAULT_USERS_PER_REQUEST]
            reserve_users = users[DEFAULT_USERS_PER_REQUEST:DEFAULT_USERS_PER_REQUEST + RESERVE_USERS_PER_REQUEST]
        else:
            # Обратный порядок
            selected_users = list(reversed(users))[:DEFAULT_USERS_PER_REQUEST]
            reserve_users = list(reversed(users))[DEFAULT_USERS_PER_REQUEST:DEFAULT_USERS_PER_REQUEST + RESERVE_USERS_PER_REQUEST]
            
        # Создаем распределения
        distributions = []
        
        # Устанавливаем время истечения срока действия распределения
        expires_at = datetime.utcnow() + timedelta(hours=24)  # Распределение действительно 24 часа
        
        # Основной поток
        for user in selected_users:
            distribution = Distribution(
                request_id=request_id,
                user_id=user.id,
                status="отправлено",
                expires_at=expires_at
            )
            self.session.add(distribution)
            distributions.append(distribution)
            
        # Резервный поток (если основной поток не заполнен)
        if len(selected_users) < DEFAULT_USERS_PER_REQUEST:
            remaining = DEFAULT_USERS_PER_REQUEST - len(selected_users)
            for user in reserve_users[:remaining]:
                distribution = Distribution(
                    request_id=request_id,
                    user_id=user.id,
                    status="отправлено",
                    expires_at=expires_at
                )
                self.session.add(distribution)
                distributions.append(distribution)
                
        self.session.commit()
        
        logger.info(f"Заявка #{request_id} распределена между {len(distributions)} пользователями")
        return distributions
        
    def _get_users_for_request(self, request: Request) -> List[User]:
        """
        Получает список пользователей, подходящих для заявки
        
        Args:
            request: Заявка
            
        Returns:
            List[User]: Список пользователей
        """
        # Базовый запрос: активные пользователи
        query = self.session.query(User).filter(User.is_active == True)
        
        # Фильтр по категории
        if request.category_id:
            query = query.join(User.categories).filter(Category.id == request.category_id)
            
        # Фильтр по городу
        if request.city_id:
            query = query.join(User.cities).filter(City.id == request.city_id)
            
        # Фильтр по подкатегориям
        if request.subcategories:
            # Получаем ID всех подкатегорий заявки
            subcategory_ids = [sc.id for sc in request.subcategories]
            if subcategory_ids:
                # Фильтруем пользователей, у которых есть хотя бы одна из подкатегорий заявки
                query = query.join(User.subcategories).filter(SubCategory.id.in_(subcategory_ids))
        
        # Дополнительные фильтры по специфическим критериям
        if request.house_type:
            # Находим подкатегорию с типом 'house_type' и значением, соответствующим заявке
            query = query.join(User.subcategories).filter(
                and_(
                    SubCategory.type == 'house_type',
                    SubCategory.name == request.house_type
                )
            )
            
        if request.has_design_project is not None:
            # Находим подкатегорию с типом 'design_project'
            design_subcategory_name = "С дизайн-проектом" if request.has_design_project else "Без дизайн-проекта"
            query = query.join(User.subcategories).filter(
                and_(
                    SubCategory.type == 'design_project',
                    SubCategory.name == design_subcategory_name
                )
            )
            
        if request.area_value:
            # Находим подкатегории с типом 'area' и подходящим диапазоном значений
            query = query.join(User.subcategories).filter(
                and_(
                    SubCategory.type == 'area',
                    or_(
                        and_(
                            SubCategory.min_value <= request.area_value,
                            SubCategory.max_value >= request.area_value
                        ),
                        and_(
                            SubCategory.min_value <= request.area_value,
                            SubCategory.max_value.is_(None)
                        ),
                        and_(
                            SubCategory.min_value.is_(None),
                            SubCategory.max_value >= request.area_value
                        )
                    )
                )
            )
            
        # Получаем всех подходящих пользователей
        users = query.all()
        
        # Если нет пользователей с точным совпадением, ищем с частичным совпадением
        if not users:
            logger.info(f"Не найдено пользователей с точным совпадением для заявки #{request.id}, ищем с частичным совпадением")
            
            # Сначала пробуем найти по основным критериям (категория и город)
            query = self.session.query(User).filter(User.is_active == True)
            
            if request.category_id:
                query = query.join(User.categories).filter(Category.id == request.category_id)
                users = query.all()
                
            if not users and request.city_id:
                query = self.session.query(User).filter(User.is_active == True)
                query = query.join(User.cities).filter(City.id == request.city_id)
                users = query.all()
                
            # Если все еще нет пользователей, пробуем найти по подкатегориям
            if not users and request.subcategories:
                subcategory_ids = [sc.id for sc in request.subcategories]
                if subcategory_ids:
                    query = self.session.query(User).filter(User.is_active == True)
                    query = query.join(User.subcategories).filter(SubCategory.id.in_(subcategory_ids))
                    users = query.all()
            
        # Если все еще нет пользователей, возвращаем всех активных
        if not users:
            logger.warning(f"Не найдено подходящих пользователей для заявки #{request.id}, возвращаем всех активных")
            users = self.session.query(User).filter(User.is_active == True).all()
            
        # Сортируем пользователей по количеству полученных заявок (в порядке возрастания)
        users.sort(key=lambda user: len(user.distributions))
        
        return users
        
    def get_request_statistics(self) -> Dict[str, Any]:
        """
        Получает статистику по заявкам
        
        Returns:
            Dict[str, Any]: Статистика
        """
        # Общее количество заявок
        total_requests = self.session.query(func.count(Request.id)).scalar()
        
        # Количество заявок по статусам
        status_counts = {}
        for status in RequestStatus:
            count = self.session.query(func.count(Request.id)).filter(Request.status == status).scalar()
            status_counts[status.value] = count
            
        # Количество заявок по категориям
        category_counts = {}
        categories = self.session.query(Category).all()
        for category in categories:
            count = self.session.query(func.count(Request.id)).filter(Request.category_id == category.id).scalar()
            category_counts[category.name] = count
            
        # Количество заявок по городам
        city_counts = {}
        cities = self.session.query(City).all()
        for city in cities:
            count = self.session.query(func.count(Request.id)).filter(Request.city_id == city.id).scalar()
            city_counts[city.name] = count
            
        # Средняя площадь
        avg_area = self.session.query(func.avg(Request.area)).scalar() or 0
        
        # Средняя стоимость
        avg_cost = self.session.query(func.avg(Request.estimated_cost)).scalar() or 0
        
        # Статистика по распределениям
        total_distributions = self.session.query(func.count(Distribution.id)).scalar()
        accepted_distributions = self.session.query(func.count(Distribution.id)).filter(Distribution.status == "принято").scalar()
        rejected_distributions = self.session.query(func.count(Distribution.id)).filter(Distribution.status == "отклонено").scalar()
        
        return {
            "total_requests": total_requests,
            "status_counts": status_counts,
            "category_counts": category_counts,
            "city_counts": city_counts,
            "avg_area": round(avg_area, 2),
            "avg_cost": round(avg_cost, 2),
            "total_distributions": total_distributions,
            "accepted_distributions": accepted_distributions,
            "rejected_distributions": rejected_distributions,
            "acceptance_rate": round(accepted_distributions / total_distributions * 100, 2) if total_distributions > 0 else 0
        }
        
    async def get_user_distributions(self, telegram_id: int) -> List[Distribution]:
        """
        Получает список распределений для пользователя
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            List[Distribution]: Список распределений
        """
        user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            logger.warning(f"Пользователь с Telegram ID {telegram_id} не найден")
            return []
            
        # Получаем распределения пользователя
        distributions = self.session.query(Distribution).filter_by(user_id=user.id).order_by(desc(Distribution.created_at)).all()
        
        # Расшифровываем персональные данные для отображения
        for distribution in distributions:
            request = distribution.request
            if not request.is_demo:
                if request.client_name:
                    request.client_name = decrypt_personal_data(request.client_name)
                if request.client_phone:
                    request.client_phone = decrypt_personal_data(request.client_phone)
                if request.address:
                    request.address = decrypt_personal_data(request.address)
                    
        return distributions
        
    async def get_distribution(self, distribution_id: int) -> Optional[Distribution]:
        """
        Получает распределение по ID
        
        Args:
            distribution_id: ID распределения
            
        Returns:
            Optional[Distribution]: Распределение или None, если не найдено
        """
        distribution = self.session.query(Distribution).filter_by(id=distribution_id).first()
        if distribution and not distribution.request.is_demo:
            # Расшифровываем персональные данные
            request = distribution.request
            if request.client_name:
                request.client_name = decrypt_personal_data(request.client_name)
            if request.client_phone:
                request.client_phone = decrypt_personal_data(request.client_phone)
            if request.address:
                request.address = decrypt_personal_data(request.address)
                
        return distribution
        
    async def update_distribution_status(self, distribution_id: int, status: str) -> Optional[Distribution]:
        """
        Обновляет статус распределения
        
        Args:
            distribution_id: ID распределения
            status: Новый статус
            
        Returns:
            Optional[Distribution]: Обновленное распределение или None, если не найдено
        """
        distribution = self.session.query(Distribution).filter_by(id=distribution_id).first()
        if not distribution:
            logger.warning(f"Распределение #{distribution_id} не найдено")
            return None
            
        # Обновляем статус
        distribution.status = status
        
        # Если статус "принято", обновляем статус заявки
        if status == "принято":
            distribution.is_converted = True
            distribution.request.status = RequestStatus.IN_PROGRESS
            
        # Если статус "отклонено", проверяем, остались ли активные распределения
        elif status == "отклонено":
            active_distributions = self.session.query(func.count(Distribution.id)).filter(
                Distribution.request_id == distribution.request_id,
                Distribution.status.in_(["отправлено", "просмотрено"])
            ).scalar()
            
            # Если нет активных распределений, обновляем статус заявки
            if active_distributions == 0:
                # Проверяем, есть ли принятые распределения
                accepted_distributions = self.session.query(func.count(Distribution.id)).filter(
                    Distribution.request_id == distribution.request_id,
                    Distribution.status == "принято"
                ).scalar()
                
                if accepted_distributions == 0:
                    # Если нет принятых распределений, помечаем заявку как неактуальную
                    distribution.request.status = RequestStatus.NOT_ACTUAL
                    
        # Если статус "просмотрено", обновляем время ответа
        elif status == "просмотрено":
            # Вычисляем время ответа в секундах
            response_time = (datetime.utcnow() - distribution.created_at).total_seconds()
            distribution.response_time = int(response_time)
            
        distribution.updated_at = datetime.utcnow()
        await self.session.commit()
        
        logger.info(f"Статус распределения #{distribution_id} обновлен на '{status}'")
        return distribution 