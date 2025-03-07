"""
Скрипт для отладки состояний пользователя
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
from aiogram.filters import Command, CommandStart

from config import TELEGRAM_BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция"""
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
            "Привет! Это отладочный бот. Выберите опцию из меню.",
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
    
    # Запускаем поллинг
    logger.info("Запускаем отладочного бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 