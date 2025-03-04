import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import threading
import time
import asyncio
import pytz
import traceback
from zoneinfo import ZoneInfo
from telegram.ext import Defaults

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from bot.handlers.admin_handlers import get_admin_conversation_handler
from bot.handlers.user_handlers import get_user_conversation_handler, show_main_menu
from bot.handlers.chat_handlers import handle_chat_message
from bot.utils.github_utils import start_github_sync, push_changes_to_github
from bot.models import init_db, get_session, Category, City
from bot.services.request_service import RequestService
from bot.utils.demo_utils import generate_demo_request, should_generate_demo_request
from config import (
    TELEGRAM_BOT_TOKEN, 
    ADMIN_IDS, 
    DEMO_MODE,
    DEFAULT_CATEGORIES,
    DEFAULT_CITIES,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Устанавливаем уровень логирования для библиотеки python-telegram-bot
logging.getLogger('telegram').setLevel(logging.INFO)
logging.getLogger('httpx').setLevel(logging.INFO)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке обновления: {context.error}")
    logger.error(f"Обновление: {update}")
    logger.error(f"Контекст: {context}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Простой обработчик текстовых сообщений"""
    logger.info(f"Получено сообщение: {update.message.text}")
    await update.message.reply_text(f"Вы написали: {update.message.text}")

def initialize_database() -> None:
    """Инициализирует базу данных и создает начальные данные"""
    # Инициализируем базу данных
    engine = init_db()
    session = get_session()
    
    # Создаем категории, если их нет
    for category_name in DEFAULT_CATEGORIES:
        if not session.query(Category).filter(Category.name == category_name).first():
            category = Category(name=category_name, is_active=True)
            session.add(category)
    
    # Создаем города, если их нет
    for city_name in DEFAULT_CITIES:
        if not session.query(City).filter(City.name == city_name).first():
            city = City(name=city_name, is_active=True)
            session.add(city)
    
    session.commit()
    logger.info("База данных инициализирована")

async def demo_request_generator(bot: Bot) -> None:
    """Генератор демо-заявок"""
    if not DEMO_MODE:
        return
    
    while True:
        # Определяем, сколько заявок нужно сгенерировать сегодня
        min_requests, max_requests = DEMO_REQUESTS_PER_DAY
        total_requests = random.randint(min_requests, max_requests)
        
        # Вычисляем интервал между заявками
        now = datetime.now()
        start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=18, minute=0, second=0, microsecond=0)
        
        if now > end_time:
            # Если сейчас после 18:00, то генерируем заявки на завтра
            start_time = start_time + timedelta(days=1)
            end_time = end_time + timedelta(days=1)
        
        # Вычисляем интервал между заявками в секундах
        interval_seconds = (end_time - start_time).total_seconds() / total_requests
        
        # Ждем до начала рабочего дня
        if now < start_time:
            sleep_seconds = (start_time - now).total_seconds()
            logger.info(f"Ждем до начала рабочего дня: {sleep_seconds} секунд")
            await asyncio.sleep(sleep_seconds)
        
        # Генерируем заявки в течение дня
        for _ in range(total_requests):
            if should_generate_demo_request():
                session = get_session()
                request_service = RequestService(session)
                
                # Генерируем демо-заявку
                demo_data = generate_demo_request()
                
                # Создаем заявку
                request = request_service.create_request(demo_data)
                
                # Распределяем заявку
                distributions = request_service.distribute_request(request.id)
                
                logger.info(f"Создана демо-заявка: ID={request.id}, распределена {len(distributions)} пользователям")
            
            # Ждем до следующей заявки
            await asyncio.sleep(interval_seconds)

def main() -> None:
    """Основная функция приложения"""
    try:
        # Инициализируем базу данных
        initialize_database()
        
        # Создаем объект Defaults с часовым поясом
        defaults = Defaults(tzinfo=pytz.timezone('Europe/Moscow'))
        
        # Создаем Application и передаем ему токен бота и настройки по умолчанию
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).defaults(defaults).build()
        
        # Добавляем обработчики диалогов
        logger.info("Добавляем обработчик пользовательских диалогов")
        user_handler = get_user_conversation_handler()
        application.add_handler(user_handler)
        
        logger.info("Добавляем обработчик админских диалогов")
        admin_handler = get_admin_conversation_handler()
        application.add_handler(admin_handler)
        
        # Добавляем обработчик сообщений из чатов
        application.add_handler(MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT,
            handle_chat_message
        ))
        
        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Добавляем отдельный обработчик команды /start для диагностики
        async def direct_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            logger.info(f"Прямой обработчик /start вызван пользователем {update.effective_user.id}")
            await update.message.reply_text(
                f"Привет, {update.effective_user.first_name}! Это прямой обработчик команды /start.\n"
                "Если вы видите это сообщение, значит основной обработчик не работает.\n"
                "Попробуйте использовать команду /menu для доступа к главному меню."
            )
        
        application.add_handler(CommandHandler('direct_start', direct_start_handler))
        application.add_handler(CommandHandler('menu', lambda u, c: show_main_menu(u, c)))
        application.add_handler(CommandHandler('start', direct_start_handler))
        
        # Запускаем синхронизацию с GitHub
        # start_github_sync()  # Отключено, так как вызывает проблемы
        
        # Запускаем бота
        logger.info("Запуск системы распределения заявок...")
        logger.info(f"Токен бота: {TELEGRAM_BOT_TOKEN[:5]}...{TELEGRAM_BOT_TOKEN[-5:]}")
        
        # Запускаем демо-генератор заявок в отдельном потоке
        if DEMO_MODE:
            # Создаем и запускаем демо-генератор в отдельном потоке
            demo_thread = threading.Thread(
                target=lambda: asyncio.run(demo_request_generator(application.bot)),
                daemon=True
            )
            demo_thread.start()
            logger.info("Демо-генератор заявок запущен")
        
        # Запускаем бота и ждем, пока он не будет остановлен
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка в main(): {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())
        # Отправляем изменения в GitHub при ошибке
        push_changes_to_github("Автоматическое обновление после ошибки") 