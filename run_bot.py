"""
Скрипт для запуска бота с обработкой ошибок и логированием
"""
import os
import sys
import logging
import traceback
import time
from datetime import datetime
import asyncio

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

def run_migrations():
    """Применяет миграции базы данных"""
    try:
        logger.info("Применение миграций базы данных...")
        from apply_migrations import apply_migrations
        apply_migrations()
        logger.info("Миграции успешно применены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при применении миграций: {e}")
        traceback.print_exc()
        return False

async def main():
    """Основная функция скрипта"""
    logger.info("=" * 50)
    logger.info(f"Запуск скрипта в {datetime.now()}")
    
    # Проверка и применение миграций
    if not run_migrations():
        logger.error("Ошибка при применении миграций")
        return
    
    # Запуск бота
    try:
        logger.info("Запуск бота...")
        from main import main as bot_main
        await bot_main()
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        traceback.print_exc()
    finally:
        logger.info("Скрипт завершил работу")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}")
        traceback.print_exc() 