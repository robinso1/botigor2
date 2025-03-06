"""
Скрипт для применения новой миграции
"""
import os
import sys
import logging
from alembic import command
from alembic.config import Config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def apply_migrations():
    """Применяет миграции базы данных"""
    try:
        logger.info("Применение миграций базы данных...")
        
        # Создаем конфигурацию Alembic
        alembic_cfg = Config("alembic.ini")
        
        # Применяем миграции
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Миграции успешно применены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при применении миграций: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    apply_migrations() 