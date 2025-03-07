"""
Скрипт для запуска бота с обработкой ошибок и логированием
"""
import os
import sys
import logging
import traceback
import time
import asyncio
import socket
import signal
import fcntl
import psutil
import re
import subprocess
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.exceptions import TelegramAPIError

from bot.handlers import setup_handlers
from bot.middlewares import setup_middlewares
from bot.database.setup import setup_database
from bot.services.scheduler import start_scheduler, stop_scheduler
from bot.services.demo_service import generate_demo_requests
from bot.services.info_service import start_info_service
from bot.utils.github_utils import start_github_sync
from config import TELEGRAM_BOT_TOKEN, ADMIN_IDS, DEMO_MODE, setup_logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Файл блокировки
LOCK_FILE = "/tmp/telegram_bot.lock"

def kill_other_bot_instances():
    """Завершает другие экземпляры бота"""
    current_pid = os.getpid()
    killed = False
    
    try:
        # Находим все процессы Python, запускающие run_bot.py
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Пропускаем текущий процесс
                if proc.info['pid'] == current_pid:
                    continue
                
                # Проверяем, является ли процесс экземпляром нашего бота
                cmdline = proc.info.get('cmdline', [])
                if cmdline and len(cmdline) > 1:
                    cmd_str = ' '.join(cmdline)
                    if 'python' in cmd_str and 'run_bot.py' in cmd_str:
                        logger.warning(f"Завершаем другой экземпляр бота (PID: {proc.info['pid']})")
                        try:
                            # Пытаемся корректно завершить процесс
                            proc.terminate()
                            killed = True
                        except psutil.NoSuchProcess:
                            pass
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        logger.error(f"Ошибка при завершении других экземпляров бота: {e}")
    
    return killed

def is_bot_running():
    """Проверяет, запущен ли уже экземпляр бота"""
    try:
        # Сначала завершаем другие экземпляры бота
        if kill_other_bot_instances():
            # Даем время на завершение процессов
            time.sleep(2)
        
        # Пытаемся создать и заблокировать файл
        try:
            lock_file = open(LOCK_FILE, "w")
            fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Если удалось, значит другой экземпляр не запущен
            # Сохраняем файловый дескриптор, чтобы блокировка сохранялась
            global lock_fd
            lock_fd = lock_file
            
            # Записываем PID в файл блокировки
            lock_file.write(str(os.getpid()))
            lock_file.flush()
            
            return False
        except IOError:
            # Если не удалось, значит файл уже заблокирован другим процессом
            logger.warning("Не удалось получить блокировку файла, возможно, бот уже запущен")
            
            # Пытаемся удалить файл блокировки, если он существует
            try:
                os.remove(LOCK_FILE)
                logger.info("Файл блокировки удален")
                
                # Пробуем снова
                return is_bot_running()
            except OSError:
                pass
            
            return True
    except Exception as e:
        logger.error(f"Ошибка при проверке запущенных экземпляров бота: {e}")
        # В случае ошибки лучше продолжить выполнение
        return False

def run_migrations():
    """Применяет миграции базы данных"""
    logger.info("Применение миграций базы данных...")
    try:
        from alembic import command
        from alembic.config import Config
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Миграции успешно применены")
    except Exception as e:
        logger.error(f"Ошибка при применении миграций: {e}")
        logger.error(traceback.format_exc())

async def main():
    """Основная функция запуска бота"""
    logger.info("=" * 50)
    logger.info(f"Запуск скрипта в {datetime.now()}")
    
    # Проверяем, запущен ли уже экземпляр бота
    if is_bot_running():
        logger.error("Бот уже запущен. Завершение работы.")
        return
    
    # Применяем миграции
    logger.info("Применение миграций базы данных...")
    run_migrations()
    
    # Запускаем бота
    logger.info("Запуск бота...")
    try:
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
        
        # Регистрируем обработчик ошибок для asyncio
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handle_asyncio_exception)
        
        # Запускаем планировщик задач
        await start_scheduler()
        
        # Запускаем сервис информационных сообщений
        await start_info_service(bot)
        
        # Запускаем синхронизацию с GitHub
        start_github_sync()
        
        # Запускаем генерацию демо-заявок, если включен демо-режим
        if DEMO_MODE:
            logger.info("Демо-режим включен, запускаем генерацию демо-заявок")
            asyncio.create_task(generate_demo_requests())
        
        # Отправляем сообщение администраторам о запуске бота
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"🤖 Бот запущен!\n\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🔄 Демо-режим: {'включен' if DEMO_MODE else 'выключен'}"
                )
                logger.info(f"Отправлено уведомление о запуске администратору {admin_id}")
            except TelegramAPIError as e:
                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")
        
        # Регистрируем обработчик сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Запускаем поллинг
        logger.info("Запускаем поллинг бота...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        logger.critical(traceback.format_exc())
    finally:
        # Останавливаем планировщик задач
        await stop_scheduler()
        
        # Удаляем файл блокировки
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            logger.info("Файл блокировки удален")

def handle_asyncio_exception(loop, context):
    """Обработчик исключений для asyncio"""
    exception = context.get('exception')
    if exception:
        logger.error(f"Необработанное исключение asyncio: {exception}")
        logger.error(f"Контекст: {context}")
    else:
        logger.error(f"Ошибка asyncio: {context['message']}")
        logger.error(f"Контекст: {context}")

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения работы"""
    logger.info("Получен сигнал завершения. Останавливаем бота...")
    
    # Удаляем файл блокировки при завершении
    try:
        if 'lock_fd' in globals():
            lock_fd.close()
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception as e:
        logger.error(f"Ошибка при удалении файла блокировки: {e}")
    
    sys.exit(0)

if __name__ == "__main__":
    # Настраиваем логирование
    setup_logging()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Необработанная ошибка: {e}")
        logger.critical(traceback.format_exc())
    finally:
        # Удаляем файл блокировки
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            logger.info("Файл блокировки удален") 