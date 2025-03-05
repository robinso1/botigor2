"""
Скрипт для запуска всех утилит обслуживания базы данных
"""
import os
import sys
import logging
import argparse
import subprocess
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("maintenance.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name, args=None):
    """Запускает указанный скрипт с аргументами"""
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    logger.info(f"Запуск скрипта: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Скрипт {script_name} выполнен успешно")
            logger.debug(f"Вывод скрипта: {result.stdout}")
        else:
            logger.error(f"Скрипт {script_name} завершился с ошибкой (код {result.returncode})")
            logger.error(f"Ошибка: {result.stderr}")
        
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Ошибка при запуске скрипта {script_name}: {e}")
        return False

def backup_database():
    """Создает резервную копию базы данных"""
    return run_script("backup_database.py")

def cleanup_demo_requests(days=7):
    """Очищает старые демо-заявки"""
    return run_script("cleanup_demo_requests.py", [str(days)])

def check_config():
    """Проверяет конфигурацию"""
    return run_script("check_config.py")

def run_migrations():
    """Применяет миграции базы данных"""
    return run_script("apply_migrations.py")

def main():
    """Основная функция скрипта"""
    parser = argparse.ArgumentParser(description="Утилиты обслуживания базы данных")
    parser.add_argument("--all", action="store_true", help="Запустить все утилиты")
    parser.add_argument("--backup", action="store_true", help="Создать резервную копию базы данных")
    parser.add_argument("--cleanup", action="store_true", help="Очистить старые демо-заявки")
    parser.add_argument("--days", type=int, default=7, help="Количество дней для очистки демо-заявок")
    parser.add_argument("--check", action="store_true", help="Проверить конфигурацию")
    parser.add_argument("--migrate", action="store_true", help="Применить миграции базы данных")
    
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info(f"Запуск утилит обслуживания в {datetime.now()}")
    
    # Если не указаны конкретные утилиты, выводим справку
    if not (args.all or args.backup or args.cleanup or args.check or args.migrate):
        parser.print_help()
        return 0
    
    results = []
    
    # Запускаем утилиты
    if args.all or args.check:
        logger.info("Запуск проверки конфигурации...")
        results.append(("Проверка конфигурации", check_config()))
    
    if args.all or args.migrate:
        logger.info("Запуск применения миграций...")
        results.append(("Применение миграций", run_migrations()))
    
    if args.all or args.backup:
        logger.info("Запуск создания резервной копии...")
        results.append(("Создание резервной копии", backup_database()))
    
    if args.all or args.cleanup:
        logger.info(f"Запуск очистки старых демо-заявок (старше {args.days} дней)...")
        results.append(("Очистка демо-заявок", cleanup_demo_requests(args.days)))
    
    # Выводим результаты
    logger.info("\nРезультаты выполнения утилит:")
    for name, success in results:
        status = "✓ УСПЕШНО" if success else "✗ ОШИБКА"
        logger.info(f"{name}: {status}")
    
    # Проверяем, все ли утилиты выполнились успешно
    all_success = all(success for _, success in results)
    
    logger.info("=" * 50)
    if all_success:
        logger.info("Все утилиты выполнены успешно")
        return 0
    else:
        logger.error("Некоторые утилиты завершились с ошибками")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 