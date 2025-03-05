"""
Модуль для работы с базой данных в middleware.
"""
import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, types
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.setup import get_session
from bot.models import User

class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для работы с базой данных.
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
        # Получаем сессию базы данных
        session_generator = get_session()
        session = await anext(session_generator)
        
        # Добавляем сессию в данные
        data["session"] = session
        
        try:
            # Получаем информацию о пользователе
            user_id = self._get_user_id(event)
            if user_id:
                # Получаем или создаем пользователя
                user = await self._get_or_create_user(session, user_id, event)
                
                # Добавляем пользователя в данные
                data["user"] = user
            
            # Вызываем обработчик
            return await handler(event, data)
        finally:
            # Закрываем сессию
            await session.close()
    
    def _get_user_id(self, event: types.TelegramObject) -> int:
        """
        Получает ID пользователя из события.
        
        Args:
            event: Событие
            
        Returns:
            int: ID пользователя или None, если не удалось получить
        """
        if isinstance(event, types.Message):
            return event.from_user.id
        elif isinstance(event, types.CallbackQuery):
            return event.from_user.id
        
        return None
    
    async def _get_or_create_user(
        self, 
        session: AsyncSession, 
        user_id: int, 
        event: types.TelegramObject
    ) -> User:
        """
        Получает или создает пользователя.
        
        Args:
            session: Сессия базы данных
            user_id: ID пользователя
            event: Событие
            
        Returns:
            User: Пользователь
        """
        from sqlalchemy import select
        
        # Ищем пользователя в базе данных
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            # Обновляем информацию о пользователе
            user = await self._update_user_info(session, user, event)
        else:
            # Создаем нового пользователя
            user = await self._create_user(session, user_id, event)
        
        return user
    
    async def _update_user_info(
        self, 
        session: AsyncSession, 
        user: User, 
        event: types.TelegramObject
    ) -> User:
        """
        Обновляет информацию о пользователе.
        
        Args:
            session: Сессия базы данных
            user: Пользователь
            event: Событие
            
        Returns:
            User: Обновленный пользователь
        """
        # Получаем информацию о пользователе из события
        telegram_user = self._get_telegram_user(event)
        if not telegram_user:
            return user
        
        # Обновляем информацию о пользователе
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        
        # Сохраняем изменения
        await session.commit()
        
        return user
    
    async def _create_user(
        self, 
        session: AsyncSession, 
        user_id: int, 
        event: types.TelegramObject
    ) -> User:
        """
        Создает нового пользователя.
        
        Args:
            session: Сессия базы данных
            user_id: ID пользователя
            event: Событие
            
        Returns:
            User: Созданный пользователь
        """
        # Получаем информацию о пользователе из события
        telegram_user = self._get_telegram_user(event)
        if not telegram_user:
            # Создаем пользователя с минимальной информацией
            user = User(
                id=user_id,
                username=None,
                first_name=None,
                last_name=None,
                is_active=True
            )
        else:
            # Создаем пользователя с информацией из Telegram
            user = User(
                id=user_id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                is_active=True
            )
        
        # Добавляем пользователя в базу данных
        session.add(user)
        await session.commit()
        
        logging.info(f"Создан новый пользователь: {user.id} ({user.username or user.first_name})")
        
        return user
    
    def _get_telegram_user(self, event: types.TelegramObject) -> types.User:
        """
        Получает объект пользователя Telegram из события.
        
        Args:
            event: Событие
            
        Returns:
            types.User: Объект пользователя Telegram или None, если не удалось получить
        """
        if isinstance(event, types.Message):
            return event.from_user
        elif isinstance(event, types.CallbackQuery):
            return event.from_user
        
        return None 