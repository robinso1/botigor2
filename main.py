import os
import sys
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import threading
import time
import traceback
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties

from config import (
    TELEGRAM_BOT_TOKEN,
    ADMIN_IDS,
    DEMO_MODE,
    GITHUB_TOKEN,
    GITHUB_REPO,
    DEFAULT_CATEGORIES,
    DEFAULT_CITIES,
    DEMO_GENERATION_INTERVALS,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE,
    DEBUG_MODE
)

from bot.models import (
    init_db,
    get_session,
    Category,
    City,
    RequestStatus,
    DistributionStatus
)

from bot.utils import (
    push_changes_to_github,
    get_repo_info,
    start_github_sync,
    generate_demo_request,
    should_generate_demo_request,
    cleanup_old_demo_requests,
    encrypt_personal_data,
    decrypt_personal_data,
    mask_phone_number
)

from bot.services.request_service import RequestService
from bot.services.user_service import UserService
from bot.handlers import setup_handlers
from bot.middlewares import setup_middlewares

# Получаем логгер
logger = logging.getLogger(__name__)

# Настройка логирования
def setup_logging():
    # Создаем форматтер для логов
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    
    # Очищаем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Добавляем обработчик для вывода в файл
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Добавляем обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Настраиваем логгеры библиотек
    if DEBUG_MODE:
        # В режиме отладки устанавливаем более подробное логирование для некоторых библиотек
        logging.getLogger("aiogram").setLevel(logging.DEBUG)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        # В обычном режиме устанавливаем менее подробное логирование
        logging.getLogger("aiogram").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logging.info(f"Логирование настроено. Уровень: {LOG_LEVEL}")

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
    logger.info("Запущен генератор демо-заявок")
    
    while True:
        try:
            # Проверяем, включен ли демо-режим
            if not DEMO_MODE:
                logger.info("Демо-режим отключен, генератор заявок приостановлен")
                await asyncio.sleep(300)  # Проверяем каждые 5 минут
                continue
                
            # Проверяем, нужно ли генерировать заявку
            if not should_generate_demo_request():
                # Ждем минуту перед следующей проверкой
                logger.debug("Еще не время для генерации новой демо-заявки")
                await asyncio.sleep(60)
                continue
            
            # Генерируем демо-заявку
            logger.info("Генерация новой демо-заявки...")
            demo_data = generate_demo_request()
            if not demo_data:
                logger.warning("Не удалось сгенерировать демо-заявку")
                await asyncio.sleep(60)
                continue
            
            # Шифруем персональные данные
            if 'phone' in demo_data:
                demo_data['phone'] = encrypt_personal_data(demo_data['phone'])
            
            # Создаем и распределяем заявку
            session = get_session()
            request_service = RequestService(session)
            
            try:
                # Создаем заявку
                request = await request_service.create_request(demo_data)
                
                # Распределяем заявку
                distributions = request_service.distribute_request(request.id)
                
                logger.info(f"Создана демо-заявка: ID={request.id}, распределена {len(distributions)} пользователям")
                
                # Очищаем старые демо-заявки
                cleanup_old_demo_requests()
            except Exception as inner_e:
                logger.error(f"Ошибка при создании или распределении демо-заявки: {inner_e}")
                session.rollback()
            finally:
                session.close()
            
            # Определяем интервал до следующей проверки
            interval_seconds = random.randint(
                DEMO_GENERATION_INTERVALS["min"] // 2,  # Половина минимального интервала
                DEMO_GENERATION_INTERVALS["min"]
            )
            
            logger.info(f"Следующая проверка через {interval_seconds} секунд")
            
            # Ждем до следующей проверки
            await asyncio.sleep(interval_seconds)
            
        except Exception as e:
            logger.error(f"Ошибка в генераторе демо-заявок: {e}")
            await asyncio.sleep(300)  # Ждем 5 минут при ошибке

async def set_bot_commands(bot: Bot):
    """Устанавливает команды бота"""
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="menu", description="Показать главное меню"),
        BotCommand(command="help", description="Показать справку"),
        BotCommand(command="admin", description="Панель администратора (только для админов)")
    ]
    await bot.set_my_commands(commands)
    logger.info("Команды бота установлены")

async def main():
    # Настройка логирования
    setup_logging()
    
    # Проверка наличия токена
    if not TELEGRAM_BOT_TOKEN:
        logging.critical("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return
    
    # Инициализация базы данных
    initialize_database()
    
    # Инициализация бота и диспетчера
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    # Создаем хранилище состояний
    storage = MemoryStorage()
    
    # Создаем диспетчер с хранилищем состояний
    dp = Dispatcher(storage=storage)
    
    try:
        # Регистрация обработчиков
        router = setup_handlers()
        dp.include_router(router)
        
        # Регистрация middleware
        setup_middlewares(router)
        
        # Установка команд бота
        await set_bot_commands(bot)
        
        # Запуск генератора демо-заявок в отдельной задаче
        if DEMO_MODE:
            demo_task = asyncio.create_task(demo_request_generator(bot))
            logger.info("Запущен генератор демо-заявок")
        
        # Запуск синхронизации с GitHub
        if GITHUB_TOKEN and GITHUB_REPO:
            start_github_sync()
            logger.info("Запущена синхронизация с GitHub")
        
        # Запуск бота
        logger.info("Бот запущен!")
        if DEBUG_MODE:
            logger.info("Работа в режиме отладки")
        
        # Запускаем поллинг
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        logger.critical(traceback.format_exc())
    finally:
        # Отменяем все задачи
        if DEMO_MODE and 'demo_task' in locals():
            demo_task.cancel()
        
        # Закрываем сессию бота
        await bot.session.close()
        
        # Закрываем хранилище состояний
        await storage.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Необработанная ошибка: {e}")
        logger.critical(traceback.format_exc()) 