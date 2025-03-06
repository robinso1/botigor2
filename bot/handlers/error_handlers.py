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
    
    # Определяем тип ошибки и соответствующее сообщение
    user_message = "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
    
    if "storage" in str(exception).lower() or "state" in str(exception).lower():
        user_message = "Произошла ошибка при обработке состояния. Пожалуйста, начните сначала с команды /start"
    elif isinstance(exception, TelegramAPIError):
        user_message = "Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже."
    
    # Пытаемся отправить сообщение пользователю
    try:
        if isinstance(update, types.Message):
            await update.answer(user_message)
        elif isinstance(update, types.CallbackQuery):
            await update.answer(user_message, show_alert=True)
            await update.message.edit_text(user_message)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")
    
    # Отправляем уведомление администраторам
    try:
        # Формируем подробное сообщение для администраторов
        trace = traceback.format_exc()
        # Ограничиваем длину трейса до 300 символов
        if len(trace) > 300:
            trace = trace[:297] + "..."
        
        admin_msg = (
            f"❌ *Ошибка в боте*\n\n"
            f"*Тип ошибки:* `{type(exception).__name__}`\n"
            f"*Сообщение:* `{str(exception)}`\n\n"
            f"*Обновление:* `{str(update)[:100]}`\n\n"
            f"*Трассировка:*\n`{trace}`"
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