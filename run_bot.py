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
from datetime import datetime

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

# Порт для проверки запущенных экземпляров
LOCK_PORT = 12345

def is_bot_running():
    """Проверяет, запущен ли уже экземпляр бота"""
    try:
        # Пытаемся создать сокет на указанном порту
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', LOCK_PORT))
        sock.listen(1)
        # Если удалось, значит другой экземпляр не запущен
        return False
    except socket.error:
        # Если не удалось, значит порт занят другим экземпляром
        return True

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
        # Импортируем main из main.py
        from main import main as run_bot
        await run_bot()
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        logger.critical(traceback.format_exc())

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения работы"""
    logger.info("Получен сигнал завершения. Останавливаем бота...")
    sys.exit(0)

if __name__ == "__main__":
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Необработанная ошибка: {e}")
        logger.critical(traceback.format_exc()) 