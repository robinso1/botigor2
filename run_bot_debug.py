"""
Скрипт для запуска бота в режиме отладки с расширенным логированием
"""
import os
import sys
import logging
import traceback
from datetime import datetime

# Настройка расширенного логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # Устанавливаем уровень DEBUG для более подробного логирования
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настраиваем логирование для библиотек
logging.getLogger('telegram').setLevel(logging.DEBUG)
logging.getLogger('httpx').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

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

def run_bot():
    """Запускает бота в режиме отладки"""
    try:
        logger.info("Запуск бота в режиме отладки...")
        
        # Устанавливаем переменные окружения для режима отладки
        os.environ['DEBUG_MODE'] = 'True'
        
        # Импортируем и запускаем основную функцию
        from main import main
        main()
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        traceback.print_exc()
        return False
    return True

def main():
    """Основная функция скрипта"""
    logger.info("=" * 50)
    logger.info(f"Запуск бота в режиме отладки в {datetime.now()}")
    
    # Проверяем наличие необходимых переменных окружения
    from config import TELEGRAM_BOT_TOKEN
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Не указан TELEGRAM_BOT_TOKEN в переменных окружения")
        sys.exit(1)
    
    # Применяем миграции
    if not run_migrations():
        logger.error("Не удалось применить миграции, завершение работы")
        sys.exit(1)
    
    # Запускаем бота
    if not run_bot():
        logger.error("Не удалось запустить бота, завершение работы")
        sys.exit(1)
    
    logger.info("Бот завершил работу")
    logger.info("=" * 50)

if __name__ == "__main__":
    main() 