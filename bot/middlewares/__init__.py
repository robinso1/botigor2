"""
Промежуточное ПО для бота
"""
import logging
import traceback
from typing import Any, Dict, Callable, Awaitable, Optional, Union
from aiogram import Router, types, BaseMiddleware
from aiogram.types import TelegramObject, User, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.setup import async_session
from bot.models import User as DbUser
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

class StateMiddleware(BaseMiddleware):
    """Промежуточное ПО для работы с состояниями"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обрабатывает событие и добавляет состояние в данные
        
        Args:
            handler: Обработчик события
            event: Событие
            data: Данные события
            
        Returns:
            Any: Результат обработки события
        """
        try:
            # Получаем состояние из data
            state = data.get("state")
            
            if state:
                # Логируем текущее состояние
                current_state = await state.get_state()
                logger.debug(f"Текущее состояние: {current_state}")
                
                # Добавляем состояние в data
                data["current_state"] = current_state
            
            # Вызываем следующий обработчик
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка в StateMiddleware: {e}")
            logger.error(traceback.format_exc())
            # Продолжаем обработку события
            return await handler(event, data)

class DatabaseMiddleware(BaseMiddleware):
    """Промежуточное ПО для работы с базой данных"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обрабатывает событие и добавляет сессию базы данных в данные
        
        Args:
            handler: Обработчик события
            event: Событие
            data: Данные события
            
        Returns:
            Any: Результат обработки события
        """
        try:
            # Создаем сессию базы данных
            async with async_session() as session:
                # Добавляем сессию в data
                data["session"] = session
                
                # Вызываем следующий обработчик
                return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка в DatabaseMiddleware: {e}")
            logger.error(traceback.format_exc())
            # Продолжаем обработку события
            return await handler(event, data)

class LoggingMiddleware(BaseMiddleware):
    """Промежуточное ПО для логирования событий"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обрабатывает событие и логирует его
        
        Args:
            handler: Обработчик события
            event: Событие
            data: Данные события
            
        Returns:
            Any: Результат обработки события
        """
        try:
            # Логируем входящее событие
            user_info = self._get_user_info(event)
            event_info = self._get_event_info(event)
            
            logger.info(f"Получено событие: {event_info} от {user_info}")
            
            # Вызываем следующий обработчик
            result = await handler(event, data)
            
            # Логируем результат обработки
            logger.info(f"Событие {event_info} от {user_info} обработано")
            
            return result
        except Exception as e:
            logger.error(f"Ошибка в LoggingMiddleware: {e}")
            logger.error(traceback.format_exc())
            # Продолжаем обработку события
            return await handler(event, data)
    
    def _get_user_info(self, event: TelegramObject) -> str:
        """
        Получает информацию о пользователе из события
        
        Args:
            event: Событие
            
        Returns:
            str: Информация о пользователе
        """
        try:
            if isinstance(event, Message):
                user = event.from_user
                return f"пользователь {user.id} ({user.username or user.first_name})"
            elif isinstance(event, CallbackQuery):
                user = event.from_user
                return f"пользователь {user.id} ({user.username or user.first_name})"
            else:
                return "неизвестный пользователь"
        except Exception as e:
            logger.error(f"Ошибка при получении информации о пользователе: {e}")
            return "неизвестный пользователь"
    
    def _get_event_info(self, event: TelegramObject) -> str:
        """
        Получает информацию о событии
        
        Args:
            event: Событие
            
        Returns:
            str: Информация о событии
        """
        try:
            if isinstance(event, Message):
                if event.text:
                    return f"сообщение '{event.text[:50]}'"
                elif event.photo:
                    return "фото"
                elif event.document:
                    return f"документ '{event.document.file_name}'"
                else:
                    return "сообщение"
            elif isinstance(event, CallbackQuery):
                return f"callback '{event.data}'"
            else:
                return f"событие {type(event).__name__}"
        except Exception as e:
            logger.error(f"Ошибка при получении информации о событии: {e}")
            return f"событие {type(event).__name__}"

class ThrottlingMiddleware(BaseMiddleware):
    """Промежуточное ПО для ограничения частоты запросов"""
    
    def __init__(self, rate_limit: float = 0.5, admin_rate_limit: float = 0.1):
        """
        Инициализирует промежуточное ПО
        
        Args:
            rate_limit: Ограничение частоты запросов (в секундах)
            admin_rate_limit: Ограничение частоты запросов для администраторов (в секундах)
        """
        self.rate_limit = rate_limit
        self.admin_rate_limit = admin_rate_limit
        self.throttled_users = {}
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обрабатывает событие и ограничивает частоту запросов
        
        Args:
            handler: Обработчик события
            event: Событие
            data: Данные события
            
        Returns:
            Any: Результат обработки события
        """
        try:
            # Получаем пользователя из события
            user_id = None
            
            if isinstance(event, Message):
                user_id = event.from_user.id
            elif isinstance(event, CallbackQuery):
                user_id = event.from_user.id
            
            # Если пользователь не определен, пропускаем ограничение
            if not user_id:
                return await handler(event, data)
            
            # Определяем ограничение для пользователя
            rate_limit = self.admin_rate_limit if user_id in ADMIN_IDS else self.rate_limit
            
            # Проверяем, не превышена ли частота запросов
            import time
            current_time = time.time()
            
            if user_id in self.throttled_users:
                last_time = self.throttled_users[user_id]
                
                if current_time - last_time < rate_limit:
                    # Частота запросов превышена, пропускаем обработку
                    logger.warning(f"Частота запросов превышена для пользователя {user_id}")
                    return None
            
            # Обновляем время последнего запроса
            self.throttled_users[user_id] = current_time
            
            # Вызываем следующий обработчик
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка в ThrottlingMiddleware: {e}")
            logger.error(traceback.format_exc())
            # Продолжаем обработку события
            return await handler(event, data)

class ErrorHandlingMiddleware(BaseMiddleware):
    """Промежуточное ПО для обработки ошибок"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обрабатывает событие и перехватывает ошибки
        
        Args:
            handler: Обработчик события
            event: Событие
            data: Данные события
            
        Returns:
            Any: Результат обработки события
        """
        try:
            # Вызываем следующий обработчик
            return await handler(event, data)
        except Exception as e:
            # Логируем ошибку
            logger.error(f"Ошибка при обработке события: {e}")
            logger.error(traceback.format_exc())
            
            # Отправляем сообщение пользователю
            try:
                if isinstance(event, Message):
                    await event.answer(
                        "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже или используйте команду /start для перезапуска бота."
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже или используйте команду /start для перезапуска бота.",
                        show_alert=True
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")
            
            # Возвращаем None, чтобы прервать цепочку обработчиков
            return None

def setup_middlewares(router: Router) -> None:
    """
    Настраивает промежуточное ПО для роутера
    
    Args:
        router: Роутер для настройки
    """
    # Регистрируем промежуточное ПО
    router.message.middleware(LoggingMiddleware())
    router.message.middleware(ErrorHandlingMiddleware())
    router.message.middleware(ThrottlingMiddleware())
    router.message.middleware(DatabaseMiddleware())
    router.message.middleware(StateMiddleware())
    
    router.callback_query.middleware(LoggingMiddleware())
    router.callback_query.middleware(ErrorHandlingMiddleware())
    router.callback_query.middleware(ThrottlingMiddleware())
    router.callback_query.middleware(DatabaseMiddleware())
    router.callback_query.middleware(StateMiddleware())
    
    # Логируем регистрацию промежуточного ПО
    logger.info("Промежуточное ПО зарегистрировано") 