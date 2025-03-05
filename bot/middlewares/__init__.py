"""
Пакет с middleware для бота
"""
from aiogram import Router
from aiogram.types import TelegramObject
from typing import Dict, Any, Callable, Awaitable
import logging

from bot.middlewares.throttling import ThrottlingMiddleware
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

class DatabaseMiddleware:
    """
    Middleware для работы с базой данных
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            # Здесь можно добавить логику для работы с сессией БД
            # Например, создание сессии и добавление её в data
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка в DatabaseMiddleware: {e}")
            raise
        finally:
            # Здесь можно закрыть сессию БД
            pass

class LoggingMiddleware:
    """
    Middleware для логирования событий
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Логируем входящее событие
        logger.debug(f"Получено событие: {event}")
        
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка при обработке события: {e}")
            raise
        finally:
            # Логируем завершение обработки
            logger.debug(f"Обработка события завершена: {event}")

def setup_middlewares(router: Router) -> None:
    """
    Настраивает middleware для роутера
    """
    # Создаем экземпляры middleware
    throttling_middleware = ThrottlingMiddleware(
        default_rate=0.5,  # Ограничение в 0.5 секунды между запросами
        admin_ids=ADMIN_IDS,  # Администраторы не ограничиваются
        admin_rate=0.1  # Для админов ограничение в 0.1 секунды
    )
    database_middleware = DatabaseMiddleware()
    logging_middleware = LoggingMiddleware()
    
    # Регистрируем middleware в порядке их выполнения
    # Throttling должен быть первым, чтобы не тратить ресурсы на обработку спама
    router.message.middleware(throttling_middleware)
    router.message.middleware(logging_middleware)
    router.message.middleware(database_middleware)
    
    # Для callback_query тоже регистрируем middleware
    router.callback_query.middleware(throttling_middleware)
    router.callback_query.middleware(logging_middleware)
    router.callback_query.middleware(database_middleware)
    
    logger.info("Middleware зарегистрированы") 