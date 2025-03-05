"""
Модуль для генерации демо-заявок.
"""
import logging
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.setup import async_session
from bot.models import Request, RequestStatus, Category, City
from bot.services.request_service import create_request, distribute_request
from bot.utils.demo_utils import generate_demo_request
from config import DEBUG_MODE

async def generate_demo_requests():
    """
    Генерирует демо-заявки.
    """
    try:
        logging.info("Запуск генерации демо-заявок")
        
        # Определяем количество заявок для генерации
        num_requests = random.randint(1, 3) if DEBUG_MODE else random.randint(1, 2)
        
        # Создаем заявки
        async with async_session() as session:
            for _ in range(num_requests):
                await generate_demo_request_with_distribution(session)
        
        logging.info(f"Сгенерировано {num_requests} демо-заявок")
    except Exception as e:
        logging.error(f"Ошибка при генерации демо-заявок: {e}")

async def generate_demo_request_with_distribution(session: AsyncSession):
    """
    Генерирует демо-заявку и распределяет ее.
    
    Args:
        session: Сессия базы данных
    """
    try:
        # Генерируем демо-заявку
        demo_request = await generate_demo_request(session)
        
        if not demo_request:
            logging.warning("Не удалось сгенерировать демо-заявку")
            return
        
        # Создаем заявку в базе данных
        request = await create_request(
            session=session,
            client_name=demo_request["client_name"],
            phone=demo_request["phone"],
            description=demo_request["description"],
            category_id=demo_request["category_id"],
            city_id=demo_request["city_id"],
            is_demo=True
        )
        
        if not request:
            logging.warning("Не удалось создать демо-заявку в базе данных")
            return
        
        # Распределяем заявку
        await distribute_request(session, request.id)
        
        logging.info(f"Демо-заявка #{request.id} успешно создана и распределена")
    except Exception as e:
        logging.error(f"Ошибка при создании и распределении демо-заявки: {e}")

async def cleanup_demo_requests(days: int = 7):
    """
    Очищает старые демо-заявки.
    
    Args:
        days: Количество дней, после которых заявки считаются старыми
    """
    try:
        logging.info(f"Запуск очистки демо-заявок старше {days} дней")
        
        # Определяем дату, до которой нужно удалить заявки
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Удаляем старые демо-заявки
        async with async_session() as session:
            from sqlalchemy import delete, select
            
            # Получаем ID старых демо-заявок
            result = await session.execute(
                select(Request.id)
                .where(Request.is_demo == True)
                .where(Request.created_at < cutoff_date)
            )
            request_ids = [row[0] for row in result.fetchall()]
            
            if not request_ids:
                logging.info("Нет демо-заявок для удаления")
                return
            
            # Удаляем связанные распределения
            from bot.models import Distribution
            await session.execute(
                delete(Distribution)
                .where(Distribution.request_id.in_(request_ids))
            )
            
            # Удаляем заявки
            await session.execute(
                delete(Request)
                .where(Request.id.in_(request_ids))
            )
            
            await session.commit()
        
        logging.info(f"Удалено {len(request_ids)} старых демо-заявок")
    except Exception as e:
        logging.error(f"Ошибка при очистке демо-заявок: {e}") 