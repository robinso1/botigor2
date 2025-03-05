"""
Обработчики ошибок для бота
"""
import logging
import traceback
from typing import Dict, Any, Callable, Awaitable, Union, Optional
from aiogram import Router, types, F
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramAPIError

from config import ADMIN_IDS

logger = logging.getLogger(__name__)

async def error_handler(error: ErrorEvent) -> None:
    """
    Обработчик ошибок для бота
    
    Args:
        error: Объект ошибки
    """
    # Получаем информацию об ошибке
    exception = error.exception
    update = error.update
    
    # Формируем сообщение об ошибке
    error_msg = f"Ошибка при обработке обновления {update}:\n{exception}"
    
    # Логируем ошибку
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    
    # Пытаемся отправить сообщение пользователю
    try:
        # Если это сообщение
        if isinstance(update, types.Message):
            await update.answer(
                "Произошла ошибка при обработке вашего сообщения. "
                "Пожалуйста, попробуйте позже или обратитесь к администратору."
            )
        # Если это callback_query
        elif isinstance(update, types.CallbackQuery):
            await update.answer(
                "Произошла ошибка при обработке вашего запроса. "
                "Пожалуйста, попробуйте позже или обратитесь к администратору.",
                show_alert=True
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")
    
    # Отправляем уведомление администраторам
    try:
        # Формируем подробное сообщение для администраторов
        admin_msg = (
            f"❌ *Ошибка в боте*\n\n"
            f"*Тип ошибки:* `{type(exception).__name__}`\n"
            f"*Сообщение:* `{str(exception)}`\n\n"
            f"*Обновление:* `{update}`\n\n"
            f"*Трассировка:*\n`{traceback.format_exc()[:1000]}`"
        )
        
        # Отправляем сообщение всем администраторам
        for admin_id in ADMIN_IDS:
            try:
                await error.bot.send_message(
                    admin_id,
                    admin_msg,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления администратору {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления администраторам: {e}")

def register_error_handlers(router: Router) -> None:
    """
    Регистрирует обработчики ошибок
    
    Args:
        router: Роутер для регистрации обработчиков
    """
    router.errors.register(error_handler)
    logger.info("Обработчики ошибок зарегистрированы") 