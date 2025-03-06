"""
Пакет с middleware для бота
"""
from aiogram import Router
from aiogram.types import TelegramObject, Message
from aiogram.fsm.context import FSMContext
from typing import Dict, Any, Callable, Awaitable
import logging

from bot.middlewares.throttling import ThrottlingMiddleware
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

class StateMiddleware:
    """
    Middleware для обработки состояний FSM
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем состояние из data
        state: FSMContext = data.get("state")
        
        if not state:
            return await handler(event, data)
        
        try:
            # Получаем текущее состояние
            current_state = await state.get_state()
            logger.debug(f"Текущее состояние: {current_state}")
            
            # Если это сообщение и содержит команду /start, сбрасываем состояние
            if isinstance(event, Message) and event.text and event.text.startswith("/start"):
                await state.clear()
                logger.debug("Состояние сброшено по команде /start")
            
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка в StateMiddleware: {e}")
            raise

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
    state_middleware = StateMiddleware()
    database_middleware = DatabaseMiddleware()
    logging_middleware = LoggingMiddleware()
    
    # Регистрируем middleware в порядке их выполнения
    # State middleware должен быть первым для правильной обработки состояний
    router.message.middleware(state_middleware)
    router.callback_query.middleware(state_middleware)
    
    # Throttling должен быть вторым, чтобы не тратить ресурсы на обработку спама
    router.message.middleware(throttling_middleware)
    router.callback_query.middleware(throttling_middleware)
    
    # Остальные middleware
    router.message.middleware(logging_middleware)
    router.message.middleware(database_middleware)
    router.callback_query.middleware(logging_middleware)
    router.callback_query.middleware(database_middleware)
    
    logger.info("Middleware зарегистрированы") 