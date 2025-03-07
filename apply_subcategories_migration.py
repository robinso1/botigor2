"""
Скрипт для применения миграции подкатегорий
"""
import logging
import sys
import os
import subprocess
from config import setup_logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

def apply_migration():
    """Применение миграции подкатегорий"""
    try:
        # Проверяем наличие миграций
        migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations", "versions")
        if not os.path.exists(migrations_dir):
            logger.error(f"Директория миграций не найдена: {migrations_dir}")
            return False
        
        # Применяем миграции
        logger.info("Применение миграций...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Ошибка при применении миграций: {result.stderr}")
            return False
        
        logger.info(f"Миграции успешно применены: {result.stdout}")
        
        # Создаем тестовые подкатегории
        logger.info("Создание тестовых подкатегорий...")
        from create_test_subcategories import create_test_subcategories
        if not create_test_subcategories():
            logger.error("Ошибка при создании тестовых подкатегорий")
            return False
        
        logger.info("Тестовые подкатегории успешно созданы")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при применении миграции: {e}")
        return False

if __name__ == "__main__":
    logger.info("Запуск скрипта применения миграции подкатегорий")
    
    if apply_migration():
        logger.info("Скрипт успешно выполнен")
        sys.exit(0)
    else:
        logger.error("Ошибка при выполнении скрипта")
        sys.exit(1) 