"""
Скрипт для запуска бота с обработкой ошибок и логированием
"""
import os
import sys
import logging
import traceback
import time
import asyncio
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("test_bot.log"),
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

async def run_bot():
    """Запускает бота"""
    try:
        logger.info("Запуск бота...")
        
        # Импортируем main.py, но используем test_config.py
        import importlib.util
        import sys
        
        # Сохраняем оригинальный модуль config
        original_config = None
        if 'config' in sys.modules:
            original_config = sys.modules['config']
        
        # Загружаем test_config как config
        spec = importlib.util.spec_from_file_location('config', 'test_config.py')
        config = importlib.util.module_from_spec(spec)
        sys.modules['config'] = config
        spec.loader.exec_module(config)
        
        # Импортируем main и запускаем
        from main import main
        await main()
        
        # Восстанавливаем оригинальный модуль config
        if original_config:
            sys.modules['config'] = original_config
        else:
            del sys.modules['config']
            
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        traceback.print_exc()
        return False
    return True

async def main():
    """Основная функция скрипта"""
    logger.info("=" * 50)
    logger.info(f"Запуск скрипта в {datetime.now()}")
    
    # Проверяем наличие необходимых переменных окружения
    import test_config
    if not test_config.TELEGRAM_BOT_TOKEN or test_config.TELEGRAM_BOT_TOKEN == "YOUR_TEST_TOKEN_HERE":
        logger.error("Не указан TELEGRAM_BOT_TOKEN в test_config.py")
        sys.exit(1)
    
    # Применяем миграции
    if not run_migrations():
        logger.error("Не удалось применить миграции, завершение работы")
        sys.exit(1)
    
    # Запускаем бота с автоматическим перезапуском при ошибках
    max_restarts = 5
    restart_count = 0
    
    while restart_count < max_restarts:
        if restart_count > 0:
            wait_time = min(30, 5 * restart_count)  # Увеличиваем время ожидания с каждым перезапуском
            logger.info(f"Перезапуск бота через {wait_time} секунд (попытка {restart_count}/{max_restarts})...")
            time.sleep(wait_time)
        
        if await run_bot():
            # Если бот завершился без ошибок, выходим из цикла
            break
        
        restart_count += 1
        logger.warning(f"Бот завершился с ошибкой, попытка перезапуска {restart_count}/{max_restarts}")
    
    if restart_count >= max_restarts:
        logger.error(f"Достигнуто максимальное количество перезапусков ({max_restarts}), завершение работы")
    
    logger.info("Скрипт завершил работу")

if __name__ == "__main__":
    asyncio.run(main()) 