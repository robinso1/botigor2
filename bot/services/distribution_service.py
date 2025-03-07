"""
Модуль для распределения заявок.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_

from bot.database.setup import async_session
from bot.models import (
    Request, 
    RequestStatus, 
    Distribution, 
    DistributionStatus, 
    User, 
    user_category, 
    user_city,
    Category,
    City,
    SubCategory
)
from bot.services.request_service import RequestService
from config import (
    DEFAULT_DISTRIBUTION_INTERVAL, 
    DEFAULT_USERS_PER_REQUEST, 
    RESERVE_USERS_PER_REQUEST,
    DEFAULT_MAX_DISTRIBUTIONS
)

logger = logging.getLogger(__name__)

async def process_distributions():
    """
    Обрабатывает распределения заявок.
    """
    try:
        logging.info("Запуск обработки распределений заявок")
        
        async with async_session() as session:
            # Обрабатываем новые заявки
            await process_new_requests(session)
            
            # Обрабатываем заявки, которые не были распределены
            await process_undistributed_requests(session)
            
            # Обрабатываем заявки, по которым истек срок распределения
            await process_expired_distributions(session)
        
        logging.info("Обработка распределений заявок завершена")
    except Exception as e:
        logging.error(f"Ошибка при обработке распределений заявок: {e}")

async def process_new_requests(session: AsyncSession):
    """
    Обрабатывает новые заявки.
    
    Args:
        session: Сессия базы данных
    """
    try:
        # Получаем новые заявки
        result = await session.execute(
            select(Request)
            .where(Request.status == RequestStatus.NEW)
            .order_by(Request.created_at)
        )
        requests = result.scalars().all()
        
        if not requests:
            logging.info("Нет новых заявок для распределения")
            return
        
        logging.info(f"Найдено {len(requests)} новых заявок для распределения")
        
        # Распределяем каждую заявку
        for request in requests:
            await distribute_request(session, request.id)
    except Exception as e:
        logging.error(f"Ошибка при обработке новых заявок: {e}")

async def process_undistributed_requests(session: AsyncSession):
    """
    Обрабатывает заявки, которые не были распределены.
    
    Args:
        session: Сессия базы данных
    """
    try:
        # Получаем заявки, которые не были распределены
        result = await session.execute(
            select(Request)
            .where(Request.status == RequestStatus.DISTRIBUTING)
            .where(~Request.distributions.any())
            .order_by(Request.created_at)
        )
        requests = result.scalars().all()
        
        if not requests:
            logging.info("Нет нераспределенных заявок")
            return
        
        logging.info(f"Найдено {len(requests)} нераспределенных заявок")
        
        # Распределяем каждую заявку
        for request in requests:
            await distribute_request(session, request.id)
    except Exception as e:
        logging.error(f"Ошибка при обработке нераспределенных заявок: {e}")

async def process_expired_distributions(session: AsyncSession):
    """
    Обрабатывает заявки, по которым истек срок распределения.
    
    Args:
        session: Сессия базы данных
    """
    try:
        # Получаем текущее время
        now = datetime.now()
        
        # Получаем заявки, по которым истек срок распределения
        result = await session.execute(
            select(Request)
            .where(Request.status == RequestStatus.DISTRIBUTING)
            .where(Request.distributions.any(
                and_(
                    Distribution.status == DistributionStatus.PENDING,
                    Distribution.expires_at < now
                )
            ))
            .order_by(Request.created_at)
        )
        requests = result.scalars().all()
        
        if not requests:
            logging.info("Нет заявок с истекшим сроком распределения")
            return
        
        logging.info(f"Найдено {len(requests)} заявок с истекшим сроком распределения")
        
        # Обрабатываем каждую заявку
        for request in requests:
            await process_expired_request(session, request)
    except Exception as e:
        logging.error(f"Ошибка при обработке заявок с истекшим сроком распределения: {e}")

async def process_expired_request(session: AsyncSession, request: Request):
    """
    Обрабатывает заявку с истекшим сроком распределения.
    
    Args:
        session: Сессия базы данных
        request: Заявка
    """
    try:
        # Получаем текущее время
        now = datetime.now()
        
        # Получаем истекшие распределения
        result = await session.execute(
            select(Distribution)
            .where(Distribution.request_id == request.id)
            .where(Distribution.status == DistributionStatus.PENDING)
            .where(Distribution.expires_at < now)
        )
        expired_distributions = result.scalars().all()
        
        if not expired_distributions:
            logging.warning(f"Не найдено истекших распределений для заявки #{request.id}")
            return
        
        logging.info(f"Найдено {len(expired_distributions)} истекших распределений для заявки #{request.id}")
        
        # Отмечаем распределения как истекшие
        for distribution in expired_distributions:
            distribution.status = DistributionStatus.EXPIRED
        
        # Проверяем, достигнуто ли максимальное количество распределений
        result = await session.execute(
            select(func.count(Distribution.id))
            .where(Distribution.request_id == request.id)
        )
        distribution_count = result.scalar_one()
        
        if distribution_count >= DEFAULT_MAX_DISTRIBUTIONS:
            # Если достигнуто максимальное количество распределений, отмечаем заявку как просроченную
            request.status = RequestStatus.EXPIRED
            logging.info(f"Заявка #{request.id} отмечена как просроченная (достигнуто максимальное количество распределений)")
        else:
            # Иначе распределяем заявку снова
            await distribute_request(session, request.id)
        
        await session.commit()
    except Exception as e:
        logging.error(f"Ошибка при обработке заявки #{request.id} с истекшим сроком распределения: {e}")

async def distribute_request(session: AsyncSession, request_id: int):
    """
    Распределяет заявку между пользователями.
    
    Args:
        session: Сессия базы данных
        request_id: ID заявки
    """
    try:
        # Создаем экземпляр сервиса для работы с заявками
        request_service = RequestService(session)
        
        # Используем метод класса для распределения заявки
        distributions = request_service.distribute_request(request_id)
        
        if distributions:
            logger.info(f"Заявка #{request_id} распределена между {len(distributions)} пользователями")
        else:
            logger.warning(f"Не удалось распределить заявку #{request_id}")
        
        return distributions
    except Exception as e:
        logger.error(f"Ошибка при распределении заявки #{request_id}: {e}")
        return []

async def get_users_for_distribution(session: AsyncSession, request: Request):
    """
    Получает пользователей, которым можно распределить заявку.
    
    Args:
        session: Сессия базы данных
        request: Заявка
        
    Returns:
        list: Список пользователей
    """
    try:
        # Получаем пользователей, которым уже была распределена заявка
        result = await session.execute(
            select(Distribution.user_id)
            .where(Distribution.request_id == request.id)
        )
        distributed_user_ids = [row[0] for row in result.fetchall()]
        
        # Получаем пользователей, которые подходят для распределения
        query = (
            select(User)
            .join(user_category, User.id == user_category.c.user_id)
            .join(user_city, User.id == user_city.c.user_id)
            .where(User.is_active == True)
            .where(user_category.c.category_id == request.category_id)
            .where(user_city.c.city_id == request.city_id)
        )
        
        # Исключаем пользователей, которым уже была распределена заявка
        if distributed_user_ids:
            query = query.where(~User.id.in_(distributed_user_ids))
        
        # Получаем пользователей
        result = await session.execute(query)
        users = result.scalars().all()
        
        # Ограничиваем количество пользователей
        max_users = DEFAULT_USERS_PER_REQUEST + RESERVE_USERS_PER_REQUEST
        return users[:max_users]
    except Exception as e:
        logging.error(f"Ошибка при получении пользователей для распределения заявки #{request.id}: {e}")
        return []

async def create_distribution(session: AsyncSession, request: Request, user: User):
    """
    Создает распределение заявки пользователю.
    
    Args:
        session: Сессия базы данных
        request: Заявка
        user: Пользователь
    """
    try:
        # Определяем срок действия распределения
        expires_at = datetime.now() + timedelta(hours=DEFAULT_DISTRIBUTION_INTERVAL)
        
        # Создаем распределение
        distribution = Distribution(
            request_id=request.id,
            user_id=user.id,
            status=DistributionStatus.PENDING,
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        session.add(distribution)
        
        logging.info(f"Создано распределение заявки #{request.id} пользователю {user.id}")
    except Exception as e:
        logging.error(f"Ошибка при создании распределения заявки #{request.id} пользователю {user.id}: {e}")

async def cleanup_old_distributions(days: int = 30):
    """
    Очищает старые распределения.
    
    Args:
        days: Количество дней, после которых распределения считаются старыми
    """
    try:
        logging.info(f"Запуск очистки распределений старше {days} дней")
        
        # Определяем дату, до которой нужно удалить распределения
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Удаляем старые распределения
        async with async_session() as session:
            result = await session.execute(
                delete(Distribution)
                .where(Distribution.created_at < cutoff_date)
                .returning(Distribution.id)
            )
            deleted_count = len(result.fetchall())
            
            await session.commit()
        
        logging.info(f"Удалено {deleted_count} старых распределений")
    except Exception as e:
        logging.error(f"Ошибка при очистке старых распределений: {e}")

class DistributionService:
    """Сервис для распределения заявок"""
    
    def __init__(self, session: AsyncSession):
        """Инициализация сервиса"""
        self.session = session
    
    def find_matching_users(self, request: Request) -> List[User]:
        """
        Находит пользователей, подходящих для заявки по категории и городу,
        а также по подкатегориям, если они указаны
        """
        try:
            # Базовый запрос для поиска пользователей по категории и городу
            query = self.session.query(User).filter(
                User.is_active == True,
                User.categories.any(Category.id == request.category_id),
                User.cities.any(City.id == request.city_id)
            )
            
            # Если у заявки есть подкатегории, учитываем их
            if request.subcategories:
                # Получаем ID подкатегорий заявки
                subcategory_ids = [sc.id for sc in request.subcategories]
                
                # Фильтруем пользователей, у которых есть все подкатегории из заявки
                for subcategory_id in subcategory_ids:
                    query = query.filter(
                        User.subcategories.any(SubCategory.id == subcategory_id)
                    )
            
            # Получаем пользователей
            matching_users = query.all()
            
            # Логируем результат
            logger.info(f"Найдено {len(matching_users)} пользователей для заявки #{request.id}")
            
            return matching_users
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске подходящих пользователей для заявки #{request.id}: {e}")
            return []
    
    def distribute_request(self, request: Request) -> List[Distribution]:
        """
        Распределяет заявку между подходящими пользователями
        """
        try:
            # Находим подходящих пользователей
            matching_users = self.find_matching_users(request)
            
            if not matching_users:
                logger.warning(f"Не найдено подходящих пользователей для заявки #{request.id}")
                return []
            
            # Создаем распределения
            distributions = []
            for user in matching_users:
                # Проверяем, не было ли уже распределения для этого пользователя и заявки
                existing_distribution = self.session.query(Distribution).filter(
                    Distribution.user_id == user.id,
                    Distribution.request_id == request.id
                ).first()
                
                if existing_distribution:
                    logger.info(f"Распределение для пользователя {user.id} и заявки #{request.id} уже существует")
                    distributions.append(existing_distribution)
                    continue
                
                # Создаем новое распределение
                distribution = Distribution(
                    user_id=user.id,
                    request_id=request.id,
                    status="отправлено",
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=24)  # Срок действия 24 часа
                )
                
                self.session.add(distribution)
                distributions.append(distribution)
            
            # Сохраняем изменения
            self.session.commit()
            
            logger.info(f"Создано {len(distributions)} распределений для заявки #{request.id}")
            
            return distributions
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при распределении заявки #{request.id}: {e}")
            self.session.rollback()
            return []
    
    def get_distribution(self, distribution_id: int) -> Optional[Distribution]:
        """
        Получает распределение по ID
        """
        try:
            return self.session.query(Distribution).filter(
                Distribution.id == distribution_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении распределения #{distribution_id}: {e}")
            return None
    
    def update_distribution_status(self, distribution_id: int, status: str) -> bool:
        """
        Обновляет статус распределения
        """
        try:
            distribution = self.get_distribution(distribution_id)
            if not distribution:
                logger.error(f"Распределение #{distribution_id} не найдено")
                return False
            
            distribution.status = status
            distribution.updated_at = datetime.now()
            
            self.session.commit()
            
            logger.info(f"Обновлен статус распределения #{distribution_id} на '{status}'")
            
            return True
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обновлении статуса распределения #{distribution_id}: {e}")
            self.session.rollback()
            return False
    
    def get_user_distributions(self, user_telegram_id: int, status: str = None) -> List[Distribution]:
        """
        Получает распределения пользователя
        """
        try:
            # Находим пользователя по telegram_id
            user = self.session.query(User).filter(
                User.telegram_id == user_telegram_id
            ).first()
            
            if not user:
                logger.error(f"Пользователь с telegram_id {user_telegram_id} не найден")
                return []
            
            # Базовый запрос
            query = self.session.query(Distribution).filter(
                Distribution.user_id == user.id
            )
            
            # Если указан статус, фильтруем по нему
            if status:
                query = query.filter(Distribution.status == status)
            
            # Получаем распределения
            distributions = query.all()
            
            return distributions
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении распределений пользователя {user_telegram_id}: {e}")
            return []
    
    def cleanup_expired_distributions(self) -> int:
        """
        Очищает просроченные распределения
        """
        try:
            # Находим просроченные распределения
            now = datetime.now()
            expired_distributions = self.session.query(Distribution).filter(
                Distribution.status == "отправлено",
                Distribution.expires_at < now
            ).all()
            
            # Обновляем статус
            count = 0
            for distribution in expired_distributions:
                distribution.status = "просрочено"
                distribution.updated_at = now
                count += 1
            
            # Сохраняем изменения
            self.session.commit()
            
            logger.info(f"Обновлено {count} просроченных распределений")
            
            return count
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при очистке просроченных распределений: {e}")
            self.session.rollback()
            return 0 