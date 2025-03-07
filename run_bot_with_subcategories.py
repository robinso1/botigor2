"""
Скрипт для запуска бота с применением миграции подкатегорий
"""
import os
import sys
import logging
import asyncio
import traceback
from datetime import datetime

from config import setup_logging
from apply_subcategories_migration import apply_migration
from run_bot_railway import main as run_bot

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

async def main():
    """Основная функция"""
    try:
        logger.info("=" * 50)
        logger.info(f"Запуск бота с применением миграции подкатегорий в {datetime.now()}")
        
        # Применяем миграцию подкатегорий
        logger.info("Применение миграции подкатегорий...")
        if not apply_migration():
            logger.error("Ошибка при применении миграции подкатегорий")
            return
        
        logger.info("Миграция подкатегорий успешно применена")
        
        # Запускаем бота
        logger.info("Запуск бота...")
        await run_bot()
    
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        # Запускаем основную функцию
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        traceback.print_exc() 