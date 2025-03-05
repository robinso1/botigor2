"""
Модуль для логирования запросов.
"""
import logging
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, types

class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для логирования запросов.
    """
    
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обрабатывает входящее событие.
        
        Args:
            handler: Обработчик события
            event: Событие
            data: Данные события
            
        Returns:
            Any: Результат обработки события
        """
        # Получаем информацию о пользователе и сообщении
        user_info = self._get_user_info(event)
        event_info = self._get_event_info(event)
        
        # Логируем входящее событие
        logging.info(f"Входящее событие: {event_info} от {user_info}")
        
        # Замеряем время выполнения обработчика
        start_time = time.time()
        
        try:
            # Вызываем обработчик
            result = await handler(event, data)
            
            # Логируем успешное выполнение
            execution_time = time.time() - start_time
            logging.info(f"Обработка события {event_info} от {user_info} завершена за {execution_time:.3f} сек")
            
            return result
        except Exception as e:
            # Логируем ошибку
            execution_time = time.time() - start_time
            logging.error(f"Ошибка при обработке события {event_info} от {user_info} "
                         f"(за {execution_time:.3f} сек): {e}")
            
            # Пробрасываем исключение дальше
            raise
    
    def _get_user_info(self, event: types.TelegramObject) -> str:
        """
        Получает информацию о пользователе из события.
        
        Args:
            event: Событие
            
        Returns:
            str: Информация о пользователе
        """
        if isinstance(event, types.Message):
            user = event.from_user
            return f"пользователь {user.id} ({user.username or user.first_name})"
        elif isinstance(event, types.CallbackQuery):
            user = event.from_user
            return f"пользователь {user.id} ({user.username or user.first_name})"
        
        return "неизвестный пользователь"
    
    def _get_event_info(self, event: types.TelegramObject) -> str:
        """
        Получает информацию о событии.
        
        Args:
            event: Событие
            
        Returns:
            str: Информация о событии
        """
        if isinstance(event, types.Message):
            if event.text:
                return f"сообщение '{event.text[:50]}'"
            elif event.photo:
                return "фото"
            elif event.document:
                return f"документ '{event.document.file_name}'"
            else:
                return "сообщение"
        elif isinstance(event, types.CallbackQuery):
            return f"callback '{event.data}'"
        
        return f"событие {type(event).__name__}" 