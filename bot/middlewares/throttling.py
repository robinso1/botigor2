"""
Middleware для ограничения частоты запросов
"""
from typing import Dict, Any, Callable, Awaitable, Optional, Union
import logging
from aiogram import types
from aiogram.types import TelegramObject, User
from bot.utils import throttle, throttle_and_wait

logger = logging.getLogger(__name__)

class ThrottlingMiddleware:
    """
    Middleware для ограничения частоты запросов
    """
    def __init__(
        self,
        default_rate: float = 0.5,
        key_prefix: str = "throttling",
        admin_ids: Optional[list] = None,
        admin_rate: Optional[float] = None
    ):
        """
        Инициализирует middleware для ограничения частоты запросов
        
        Args:
            default_rate: Минимальный интервал между запросами в секундах
            key_prefix: Префикс для ключей в хранилище
            admin_ids: Список ID администраторов, для которых не применяется ограничение
            admin_rate: Ограничение для администраторов (если None, то ограничение не применяется)
        """
        self.default_rate = default_rate
        self.key_prefix = key_prefix
        self.admin_ids = admin_ids or []
        self.admin_rate = admin_rate
        
        logger.debug(f"Инициализирован ThrottlingMiddleware с default_rate={default_rate}")
    
    def _get_user(self, obj: TelegramObject) -> Optional[User]:
        """
        Получает пользователя из объекта Telegram
        
        Args:
            obj: Объект Telegram
            
        Returns:
            Optional[User]: Пользователь, если его можно получить, иначе None
        """
        if isinstance(obj, types.Message):
            return obj.from_user
        elif isinstance(obj, types.CallbackQuery):
            return obj.from_user
        return None
    
    def _get_key(self, obj: TelegramObject) -> Optional[int]:
        """
        Получает ключ для ограничения частоты запросов
        
        Args:
            obj: Объект Telegram
            
        Returns:
            Optional[int]: ID пользователя, если его можно получить, иначе None
        """
        user = self._get_user(obj)
        if user:
            return user.id
        return None
    
    def _get_rate(self, user_id: int) -> Optional[float]:
        """
        Получает ограничение частоты для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[float]: Ограничение частоты для пользователя
        """
        if user_id in self.admin_ids:
            return self.admin_rate
        return self.default_rate
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем ключ для ограничения частоты запросов
        key = self._get_key(event)
        if not key:
            # Если не удалось получить ключ, пропускаем ограничение
            return await handler(event, data)
        
        # Получаем ограничение частоты для пользователя
        rate = self._get_rate(key)
        if rate is None:
            # Если ограничение не установлено, пропускаем ограничение
            return await handler(event, data)
        
        # Проверяем ограничение частоты
        wait_time = await throttle(key, rate)
        if wait_time is not None:
            # Если нужно ограничить запрос, отправляем сообщение
            user = self._get_user(event)
            logger.debug(f"Throttling для пользователя {user.id} ({user.username}): ожидание {wait_time:.2f} сек")
            
            # Для сообщений можем отправить уведомление о необходимости подождать
            if isinstance(event, types.Message):
                await event.answer(
                    f"Пожалуйста, не отправляйте сообщения так часто. "
                    f"Подождите {wait_time:.1f} сек."
                )
            # Для callback_query можем ответить с уведомлением
            elif isinstance(event, types.CallbackQuery):
                await event.answer(
                    f"Пожалуйста, не нажимайте кнопки так часто. "
                    f"Подождите {wait_time:.1f} сек.",
                    show_alert=True
                )
            
            # Пропускаем обработку события
            return None
        
        # Если ограничение не сработало, продолжаем обработку
        return await handler(event, data) 