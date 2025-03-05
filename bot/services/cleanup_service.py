"""
Модуль для очистки старых данных.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from bot.database.setup import async_session
from bot.models import Request, Distribution, RequestStatus
from bot.services.demo_service import cleanup_demo_requests
from bot.services.distribution_service import cleanup_old_distributions

async def cleanup_old_requests(days: int = 90):
    """
    Очищает старые заявки.
    
    Args:
        days: Количество дней, после которых заявки считаются старыми
    """
    try:
        logging.info(f"Запуск очистки заявок старше {days} дней")
        
        # Очищаем демо-заявки (они хранятся меньше)
        await cleanup_demo_requests(days=7)
        
        # Очищаем старые распределения
        await cleanup_old_distributions(days=30)
        
        # Определяем дату, до которой нужно удалить заявки
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Удаляем старые заявки
        async with async_session() as session:
            # Получаем ID старых заявок
            result = await session.execute(
                select(Request.id)
                .where(Request.created_at < cutoff_date)
                .where(Request.is_demo == False)  # Не удаляем демо-заявки, они обрабатываются отдельно
                .where(Request.status.in_([
                    RequestStatus.COMPLETED,
                    RequestStatus.CANCELLED,
                    RequestStatus.EXPIRED
                ]))
            )
            request_ids = [row[0] for row in result.fetchall()]
            
            if not request_ids:
                logging.info("Нет заявок для удаления")
                return
            
            # Удаляем связанные распределения
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
        
        logging.info(f"Удалено {len(request_ids)} старых заявок")
    except Exception as e:
        logging.error(f"Ошибка при очистке старых заявок: {e}")

async def cleanup_old_data():
    """
    Очищает все старые данные.
    """
    try:
        logging.info("Запуск очистки всех старых данных")
        
        # Очищаем старые заявки
        await cleanup_old_requests()
        
        # Очищаем старые распределения
        await cleanup_old_distributions()
        
        # Очищаем демо-заявки
        await cleanup_demo_requests()
        
        logging.info("Очистка всех старых данных завершена")
    except Exception as e:
        logging.error(f"Ошибка при очистке всех старых данных: {e}") 