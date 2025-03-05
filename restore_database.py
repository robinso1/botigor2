"""
Скрипт для восстановления базы данных из резервной копии
"""
import os
import sys
import logging
import shutil
import gzip
import glob
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("restore.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройки
BACKUP_DIR = "backups"
DB_PATH = "bot.db"
TEMP_DB_PATH = "bot.db.temp"

def list_backups():
    """Выводит список доступных резервных копий"""
    if not os.path.exists(BACKUP_DIR):
        logger.error(f"Директория с резервными копиями не найдена: {BACKUP_DIR}")
        return []
    
    backup_files = glob.glob(os.path.join(BACKUP_DIR, "bot_db_backup_*.db.gz"))
    backup_files.sort(reverse=True)  # Сортируем от новых к старым
    
    if not backup_files:
        logger.error("Резервные копии не найдены")
        return []
    
    logger.info(f"Найдено {len(backup_files)} резервных копий:")
    for i, backup in enumerate(backup_files):
        backup_name = os.path.basename(backup)
        # Извлекаем дату и время из имени файла
        date_str = backup_name.replace("bot_db_backup_", "").replace(".db.gz", "")
        date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {date_str[9:11]}:{date_str[11:13]}:{date_str[13:15]}"
        logger.info(f"{i+1}. {backup_name} (создана {date_formatted})")
    
    return backup_files

def restore_backup(backup_path):
    """Восстанавливает базу данных из резервной копии"""
    try:
        logger.info(f"Восстановление из резервной копии: {backup_path}")
        
        # Создаем резервную копию текущей базы данных, если она существует
        if os.path.exists(DB_PATH):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = f"{DB_PATH}.{timestamp}.bak"
            shutil.copy2(DB_PATH, current_backup)
            logger.info(f"Создана резервная копия текущей базы данных: {current_backup}")
        
        # Распаковываем резервную копию во временный файл
        with gzip.open(backup_path, 'rb') as f_in:
            with open(TEMP_DB_PATH, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Заменяем текущую базу данных восстановленной
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        shutil.move(TEMP_DB_PATH, DB_PATH)
        
        logger.info(f"База данных успешно восстановлена из {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при восстановлении базы данных: {e}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=" * 50)
    logger.info(f"Запуск восстановления базы данных в {datetime.now()}")
    
    # Получаем список резервных копий
    backup_files = list_backups()
    if not backup_files:
        logger.error("Нет доступных резервных копий для восстановления")
        return 1
    
    # Если указан аргумент командной строки, используем его как индекс резервной копии
    backup_index = 0  # По умолчанию используем самую свежую копию
    if len(sys.argv) > 1:
        try:
            backup_index = int(sys.argv[1]) - 1
            if backup_index < 0 or backup_index >= len(backup_files):
                logger.error(f"Некорректный индекс резервной копии: {backup_index + 1}")
                return 1
        except ValueError:
            # Если аргумент не число, считаем его путем к файлу резервной копии
            backup_path = sys.argv[1]
            if not os.path.exists(backup_path):
                logger.error(f"Файл резервной копии не найден: {backup_path}")
                return 1
            
            # Восстанавливаем из указанного файла
            if restore_backup(backup_path):
                logger.info("Восстановление завершено успешно")
                return 0
            else:
                logger.error("Не удалось восстановить базу данных")
                return 1
    
    # Восстанавливаем из выбранной резервной копии
    backup_path = backup_files[backup_index]
    if restore_backup(backup_path):
        logger.info("Восстановление завершено успешно")
        return 0
    else:
        logger.error("Не удалось восстановить базу данных")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 