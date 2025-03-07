"""
Скрипт для запуска бота с отладочной информацией
"""
import os
import sys
import logging
import asyncio
import traceback
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
from aiogram.filters import Command, CommandStart

from config import TELEGRAM_BOT_TOKEN, ADMIN_IDS, setup_logging
from bot.database.setup import setup_database
from bot.handlers import setup_handlers
from bot.middlewares import setup_middlewares

# Настройка логирования
logger = logging.getLogger(__name__)

async def main():
    """Основная функция"""
    try:
        logger.info("=" * 50)
        logger.info(f"Запуск отладочного бота в {datetime.now()}")
        
        # Настраиваем базу данных
        setup_database()
        
        # Создаем экземпляр бота и диспетчера
        session = AiohttpSession()
        bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
        dp = Dispatcher(storage=MemoryStorage())
        
        # Настраиваем обработчики и промежуточное ПО
        router = setup_handlers()
        setup_middlewares(router)
        dp.include_router(router)
        
        # Добавляем отладочный обработчик для всех сообщений
        @dp.message()
        async def debug_handler(message: Message, state=None, current_state=None):
            """Отладочный обработчик для всех сообщений"""
            logger.info(f"DEBUG: Получено сообщение '{message.text}' от пользователя {message.from_user.id}")
            logger.info(f"DEBUG: Текущее состояние: {current_state}")
            
            # Не отправляем ответ, чтобы не мешать основным обработчикам
            pass
        
        # Отправляем сообщение администраторам о запуске бота
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"🤖 Отладочный бот запущен!\n\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                logger.info(f"Отправлено уведомление о запуске администратору {admin_id}")
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")
        
        # Запускаем поллинг
        logger.info("Запускаем поллинг бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Настраиваем логирование с уровнем DEBUG
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Запускаем основную функцию
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        traceback.print_exc() 