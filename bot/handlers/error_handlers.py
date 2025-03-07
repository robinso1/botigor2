"""
Обработчики ошибок для бота
"""
import logging
import traceback
from typing import Any, Dict, Union
from aiogram import Router
from aiogram.types import ErrorEvent, Update
from aiogram.exceptions import TelegramAPIError
from aiogram.handlers import ErrorHandler

from config import ADMIN_IDS

logger = logging.getLogger(__name__)

async def error_handler(error: ErrorEvent) -> None:
    """
    Обработчик ошибок для бота
    
    Args:
        error: Объект ошибки
    """
    try:
        # Получаем информацию об ошибке
        update = error.update
        exception = error.exception
        
        # Логируем ошибку
        logger.error(f"Ошибка при обработке обновления {update}: {exception}")
        logger.error(traceback.format_exc())
        
        # Определяем тип обновления и пользователя
        user_id = None
        chat_id = None
        
        if isinstance(update, Update):
            if update.message:
                user_id = update.message.from_user.id
                chat_id = update.message.chat.id
            elif update.callback_query:
                user_id = update.callback_query.from_user.id
                chat_id = update.callback_query.message.chat.id
        
        # Отправляем сообщение пользователю
        if chat_id:
            try:
                # Получаем бота из контекста ошибки
                bot = error.bot
                
                # Отправляем сообщение пользователю
                await bot.send_message(
                    chat_id=chat_id,
                    text="Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже или используйте команду /start для перезапуска бота."
                )
                
                # Если пользователь - администратор, отправляем детали ошибки
                if user_id in ADMIN_IDS:
                    error_details = f"Ошибка: {exception}\n\nТрассировка:\n{traceback.format_exc()[:1000]}..."
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"Детали ошибки (для администратора):\n\n{error_details}"
                    )
                
                # Отправляем уведомление всем администраторам
                for admin_id in ADMIN_IDS:
                    if admin_id != user_id:  # Не отправляем дважды одному и тому же админу
                        try:
                            error_message = (
                                f"⚠️ Ошибка в боте!\n\n"
                                f"Пользователь: {user_id}\n"
                                f"Тип ошибки: {type(exception).__name__}\n"
                                f"Сообщение: {str(exception)}\n\n"
                                f"Обновление: {update}"
                            )
                            await bot.send_message(chat_id=admin_id, text=error_message[:4000])
                        except Exception as e:
                            logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")
    except Exception as e:
        logger.critical(f"Критическая ошибка в обработчике ошибок: {e}")
        logger.critical(traceback.format_exc())

class CustomErrorHandler(ErrorHandler):
    """Кастомный обработчик ошибок для бота"""
    
    async def handle(self) -> Any:
        """Обрабатывает ошибку"""
        try:
            # Получаем информацию об ошибке
            update = self.data.get("update", None)
            exception = self.data.get("exception", None)
            
            # Логируем ошибку
            logger.error(f"Ошибка при обработке обновления {update}: {exception}")
            logger.error(traceback.format_exc())
            
            # Определяем тип обновления и пользователя
            user_id = None
            chat_id = None
            
            if isinstance(update, Update):
                if update.message:
                    user_id = update.message.from_user.id
                    chat_id = update.message.chat.id
                elif update.callback_query:
                    user_id = update.callback_query.from_user.id
                    chat_id = update.callback_query.message.chat.id
            
            # Отправляем сообщение пользователю
            if chat_id:
                try:
                    # Получаем бота из контекста ошибки
                    bot = self.bot
                    
                    # Отправляем сообщение пользователю
                    await bot.send_message(
                        chat_id=chat_id,
                        text="Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже или используйте команду /start для перезапуска бота."
                    )
                    
                    # Если пользователь - администратор, отправляем детали ошибки
                    if user_id in ADMIN_IDS:
                        error_details = f"Ошибка: {exception}\n\nТрассировка:\n{traceback.format_exc()[:1000]}..."
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"Детали ошибки (для администратора):\n\n{error_details}"
                        )
                    
                    # Отправляем уведомление всем администраторам
                    for admin_id in ADMIN_IDS:
                        if admin_id != user_id:  # Не отправляем дважды одному и тому же админу
                            try:
                                error_message = (
                                    f"⚠️ Ошибка в боте!\n\n"
                                    f"Пользователь: {user_id}\n"
                                    f"Тип ошибки: {type(exception).__name__}\n"
                                    f"Сообщение: {str(exception)}\n\n"
                                    f"Обновление: {update}"
                                )
                                await bot.send_message(chat_id=admin_id, text=error_message[:4000])
                            except Exception as e:
                                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")
        except Exception as e:
            logger.critical(f"Критическая ошибка в обработчике ошибок: {e}")
            logger.critical(traceback.format_exc())

def register_error_handlers(router: Router) -> None:
    """
    Регистрирует обработчики ошибок
    
    Args:
        router: Роутер для регистрации обработчиков
    """
    # Регистрируем обработчик ошибок
    router.errors.register(error_handler)
    
    # Логируем регистрацию обработчиков
    logger.info("Обработчики ошибок зарегистрированы") 