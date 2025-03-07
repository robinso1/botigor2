"""
Модуль для генерации демо-заявок.
"""
import logging
import random
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_

from bot.database.setup import async_session
from bot.models import Request, RequestStatus, Distribution, DistributionStatus, Category, City
from bot.services.request_service import RequestService
from bot.utils.demo_utils import generate_demo_request
from config import DEBUG_MODE

logger = logging.getLogger(__name__)

async def generate_demo_requests():
    """
    Генерирует демо-заявки.
    """
    try:
        logging.info("Запуск генерации демо-заявок")
        
        # Генерируем заявку каждые 30-60 минут
        while True:
            try:
                # Генерируем случайную задержку от 30 до 60 минут
                delay = random.randint(30, 60) * 60
                if DEBUG_MODE:
                    # В режиме отладки генерируем заявки чаще
                    delay = random.randint(1, 5) * 60
                
                logging.info(f"Следующая демо-заявка будет сгенерирована через {delay // 60} минут")
                
                # Ждем указанное время
                await asyncio.sleep(delay)
                
                # Генерируем и распределяем заявку
                await generate_demo_request_with_distribution()
            except Exception as e:
                logging.error(f"Ошибка при генерации демо-заявки: {e}")
                await asyncio.sleep(60)  # Ждем минуту перед следующей попыткой
    except Exception as e:
        logging.error(f"Ошибка в генераторе демо-заявок: {e}")

async def generate_demo_request_with_distribution(session: AsyncSession = None):
    """
    Генерирует демо-заявку и распределяет ее между пользователями.
    
    Args:
        session: Сессия базы данных (опционально)
    """
    try:
        # Если сессия не передана, создаем новую
        if session is None:
            async with async_session() as session:
                return await _generate_and_distribute(session)
        else:
            return await _generate_and_distribute(session)
    except Exception as e:
        logging.error(f"Ошибка при генерации и распределении демо-заявки: {e}")
        return None

async def _generate_and_distribute(session: AsyncSession):
    """
    Внутренняя функция для генерации и распределения демо-заявки.
    
    Args:
        session: Сессия базы данных
    """
    # Генерируем данные для демо-заявки
    request_data = generate_demo_request()
    if not request_data:
        logging.warning("Не удалось сгенерировать данные для демо-заявки")
        return None
    
    # Создаем сервис для работы с заявками
    request_service = RequestService(session)
    
    # Создаем заявку
    request = await request_service.create_request(request_data)
    if not request:
        logging.warning("Не удалось создать демо-заявку")
        return None
    
    logging.info(f"Создана демо-заявка #{request.id}")
    
    # Распределяем заявку
    distributions = request_service.distribute_request(request.id)
    
    logging.info(f"Демо-заявка #{request.id} распределена между {len(distributions)} пользователями")
    
    return request

async def cleanup_demo_requests(days: int = 7):
    """
    Очищает старые демо-заявки.
    
    Args:
        days: Количество дней, после которых заявки считаются устаревшими
    """
    try:
        logging.info(f"Запуск очистки демо-заявок старше {days} дней")
        
        # Вычисляем дату, до которой нужно удалить заявки
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with async_session() as session:
            # Получаем список устаревших демо-заявок
            result = await session.execute(
                select(Request).where(
                    and_(
                        Request.is_demo == True,
                        Request.created_at < cutoff_date
                    )
                )
            )
            old_requests = result.scalars().all()
            
            if not old_requests:
                logging.info("Нет устаревших демо-заявок для удаления")
                return
            
            # Удаляем связанные распределения
            for request in old_requests:
                # Удаляем распределения
                await session.execute(
                    update(Distribution)
                    .where(Distribution.request_id == request.id)
                    .values(status=DistributionStatus.EXPIRED)
                )
                
                # Обновляем статус заявки
                request.status = RequestStatus.EXPIRED
            
            # Сохраняем изменения
            await session.commit()
            
            logging.info(f"Очищено {len(old_requests)} устаревших демо-заявок")
    except Exception as e:
        logging.error(f"Ошибка при очистке демо-заявок: {e}") 