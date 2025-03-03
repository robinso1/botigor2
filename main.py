import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import threading
import time
import asyncio
import pytz
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

from bot.models import init_db, get_session, Category, City, Request
from bot.handlers import get_user_conversation_handler, get_admin_conversation_handler, handle_chat_message
from bot.services.request_service import RequestService
from bot.utils.demo_utils import generate_demo_request, should_generate_demo_request
from bot.utils.github_utils import push_changes_to_github
from config import (
    TELEGRAM_BOT_TOKEN,
    ADMIN_IDS,
    MONITORED_CHATS,
    DEFAULT_CATEGORIES,
    DEFAULT_CITIES,
    DEMO_MODE,
    DEMO_REQUESTS_PER_DAY,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке обновления: {context.error}")

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

async def main() -> None:
    """Основная функция приложения"""
    # Инициализируем базу данных
    initialize_database()
    
    # Создаем объект Defaults с часовым поясом
    defaults = Defaults(tzinfo=pytz.timezone('Europe/Moscow'))
    
    # Создаем Application и передаем ему токен бота и настройки по умолчанию
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).defaults(defaults).build()
    
    # Добавляем обработчики
    application.add_handler(get_user_conversation_handler())
    application.add_handler(get_admin_conversation_handler())
    
    # Добавляем обработчик сообщений из чатов
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT,
        handle_chat_message
    ))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем генератор демо-заявок в отдельном потоке
    if DEMO_MODE:
        asyncio.create_task(demo_request_generator(application.bot))
    
    # Запускаем бота
    logger.info("Запуск системы распределения заявок...")
    
    # Запускаем бота и ждем, пока он не будет остановлен
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        # Отправляем изменения в GitHub при ошибке
        push_changes_to_github("Автоматическое обновление после ошибки") 