"""
Упрощенная версия скрипта запуска бота без использования состояний
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
from bot.models import User, Category, City

# Настройка логирования
logger = logging.getLogger(__name__)

async def main():
    """Основная функция"""
    try:
        logger.info("=" * 50)
        logger.info(f"Запуск упрощенного бота в {datetime.now()}")
        
        # Настраиваем базу данных
        setup_database()
        
        # Создаем экземпляр бота и диспетчера
        session = AiohttpSession()
        bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
        dp = Dispatcher(storage=MemoryStorage())
        
        # Обработчик команды /start
        @dp.message(CommandStart())
        async def start_command(message: Message):
            """Обработчик команды /start"""
            logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
            
            # Создаем клавиатуру
            keyboard = [
                [KeyboardButton(text="👤 Мой профиль")],
                [KeyboardButton(text="📋 Мои заявки")],
                [KeyboardButton(text="⚙️ Настройки")],
                [KeyboardButton(text="🔙 Вернуться в главное меню")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
            
            await message.answer(
                "Привет! Это упрощенная версия бота. Выберите опцию из меню.",
                reply_markup=reply_markup
            )
        
        # Обработчик для кнопки "Мой профиль"
        @dp.message(F.text == "👤 Мой профиль")
        async def profile_menu(message: Message):
            """Обработчик для кнопки 'Мой профиль'"""
            logger.info(f"Получена команда 'Мой профиль' от пользователя {message.from_user.id}")
            
            # Создаем клавиатуру
            keyboard = [
                [KeyboardButton(text="🔧 Выбрать категории"), KeyboardButton(text="🏙️ Выбрать города")],
                [KeyboardButton(text="📱 Изменить телефон"), KeyboardButton(text="🔍 Выбрать подкатегории")],
                [KeyboardButton(text="🔙 Вернуться в главное меню")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
            
            await message.answer(
                "Меню профиля. Выберите опцию из меню.",
                reply_markup=reply_markup
            )
        
        # Обработчик для кнопки "Выбрать категории"
        @dp.message(F.text == "🔧 Выбрать категории")
        async def select_categories(message: Message):
            """Обработчик для кнопки 'Выбрать категории'"""
            logger.info(f"Получена команда 'Выбрать категории' от пользователя {message.from_user.id}")
            
            await message.answer(
                "Здесь будет список категорий для выбора."
            )
        
        # Обработчик для кнопки "Выбрать города"
        @dp.message(F.text == "🏙️ Выбрать города")
        async def select_cities(message: Message):
            """Обработчик для кнопки 'Выбрать города'"""
            logger.info(f"Получена команда 'Выбрать города' от пользователя {message.from_user.id}")
            
            await message.answer(
                "Здесь будет список городов для выбора."
            )
        
        # Обработчик для кнопки "Изменить телефон"
        @dp.message(F.text == "📱 Изменить телефон")
        async def edit_phone(message: Message):
            """Обработчик для кнопки 'Изменить телефон'"""
            logger.info(f"Получена команда 'Изменить телефон' от пользователя {message.from_user.id}")
            
            await message.answer(
                "Введите ваш номер телефона в формате +7XXXXXXXXXX"
            )
        
        # Обработчик для кнопки "Выбрать подкатегории"
        @dp.message(F.text == "🔍 Выбрать подкатегории")
        async def select_subcategories(message: Message):
            """Обработчик для кнопки 'Выбрать подкатегории'"""
            logger.info(f"Получена команда 'Выбрать подкатегории' от пользователя {message.from_user.id}")
            
            await message.answer(
                "Здесь будет список подкатегорий для выбора."
            )
        
        # Обработчик для кнопки "Мои заявки"
        @dp.message(F.text == "📋 Мои заявки")
        async def my_requests(message: Message):
            """Обработчик для кнопки 'Мои заявки'"""
            logger.info(f"Получена команда 'Мои заявки' от пользователя {message.from_user.id}")
            
            await message.answer(
                "У вас нет активных заявок."
            )
        
        # Обработчик для кнопки "Настройки"
        @dp.message(F.text == "⚙️ Настройки")
        async def settings_menu(message: Message):
            """Обработчик для кнопки 'Настройки'"""
            logger.info(f"Получена команда 'Настройки' от пользователя {message.from_user.id}")
            
            await message.answer(
                "Меню настроек. Пока нет доступных настроек."
            )
        
        # Обработчик для кнопки "Вернуться в главное меню"
        @dp.message(F.text == "🔙 Вернуться в главное меню")
        async def back_to_main_menu(message: Message):
            """Обработчик для кнопки 'Вернуться в главное меню'"""
            logger.info(f"Получена команда 'Вернуться в главное меню' от пользователя {message.from_user.id}")
            
            # Создаем клавиатуру
            keyboard = [
                [KeyboardButton(text="👤 Мой профиль")],
                [KeyboardButton(text="📋 Мои заявки")],
                [KeyboardButton(text="⚙️ Настройки")],
                [KeyboardButton(text="🔙 Вернуться в главное меню")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
            
            await message.answer(
                "Главное меню. Выберите опцию из меню.",
                reply_markup=reply_markup
            )
        
        # Обработчик для всех остальных сообщений
        @dp.message()
        async def handle_all_messages(message: Message):
            """Обработчик для всех остальных сообщений"""
            logger.info(f"Получено сообщение '{message.text}' от пользователя {message.from_user.id}")
            
            await message.answer(
                f"Вы отправили: {message.text}\n\n"
                "Используйте кнопки меню или команду /start для начала работы."
            )
        
        # Отправляем сообщение администраторам о запуске бота
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"🤖 Упрощенный бот запущен!\n\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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
    # Настраиваем логирование
    setup_logging()
    
    try:
        # Запускаем основную функцию
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        traceback.print_exc() 