"""
Скрипт для создания резервной копии базы данных
Может запускаться по расписанию через cron или другой планировщик
"""
import os
import sys
import logging
import shutil
import sqlite3
from datetime import datetime
import gzip
import json

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("backup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройки
BACKUP_DIR = "backups"
DB_PATH = "bot.db"
MAX_BACKUPS = 10  # Максимальное количество хранимых резервных копий

def create_backup_dir():
    """Создает директорию для резервных копий, если она не существует"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logger.info(f"Создана директория для резервных копий: {BACKUP_DIR}")

def get_database_stats():
    """Получает статистику базы данных"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        stats = {
            "tables": len(tables),
            "table_stats": {}
        }
        
        # Получаем количество записей в каждой таблице
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            stats["table_stats"][table_name] = count
        
        conn.close()
        return stats
    except Exception as e:
        logger.error(f"Ошибка при получении статистики базы данных: {e}")
        return None

def create_backup():
    """Создает резервную копию базы данных"""
    try:
        # Создаем директорию для резервных копий
        create_backup_dir()
        
        # Формируем имя файла резервной копии
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"bot_db_backup_{timestamp}.db.gz")
        
        # Получаем статистику базы данных
        stats = get_database_stats()
        
        # Создаем резервную копию
        with open(DB_PATH, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Сохраняем статистику
        if stats:
            stats_path = os.path.join(BACKUP_DIR, f"bot_db_stats_{timestamp}.json")
            with open(stats_path, 'w') as f:
                json.dump(stats, f, indent=2)
        
        logger.info(f"Создана резервная копия базы данных: {backup_path}")
        
        # Удаляем старые резервные копии, если их больше MAX_BACKUPS
        cleanup_old_backups()
        
        return backup_path
    except Exception as e:
        logger.error(f"Ошибка при создании резервной копии: {e}")
        return None

def cleanup_old_backups():
    """Удаляет старые резервные копии, если их больше MAX_BACKUPS"""
    try:
        # Получаем список файлов резервных копий
        backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith("bot_db_backup_") and f.endswith(".db.gz")]
        
        # Сортируем по дате создания (от старых к новым)
        backup_files.sort()
        
        # Удаляем старые резервные копии
        if len(backup_files) > MAX_BACKUPS:
            files_to_delete = backup_files[:-MAX_BACKUPS]
            for file in files_to_delete:
                file_path = os.path.join(BACKUP_DIR, file)
                os.remove(file_path)
                
                # Удаляем также файл статистики, если он существует
                stats_file = file.replace("backup_", "stats_")
                stats_path = os.path.join(BACKUP_DIR, stats_file)
                if os.path.exists(stats_path):
                    os.remove(stats_path)
                
            logger.info(f"Удалено {len(files_to_delete)} старых резервных копий")
    except Exception as e:
        logger.error(f"Ошибка при очистке старых резервных копий: {e}")

def main():
    """Основная функция скрипта"""
    logger.info("=" * 50)
    logger.info(f"Запуск создания резервной копии в {datetime.now()}")
    
    # Проверяем наличие базы данных
    if not os.path.exists(DB_PATH):
        logger.error(f"База данных не найдена: {DB_PATH}")
        return 1
    
    # Создаем резервную копию
    backup_path = create_backup()
    
    if backup_path:
        logger.info(f"Резервная копия успешно создана: {backup_path}")
    else:
        logger.error("Не удалось создать резервную копию")
        return 1
    
    logger.info("=" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main()) 