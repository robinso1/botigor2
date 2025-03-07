"""
Скрипт для автоматического исправления проблем с ботом
"""
import logging
import sys
import os
import traceback
import subprocess
from datetime import datetime
import sqlite3

from config import setup_logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Создаем файл для логирования исправлений
fix_log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_bot_issues.log")
file_handler = logging.FileHandler(fix_log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def fix_bot_issues():
    """Автоматическое исправление проблем с ботом"""
    try:
        logger.info("=" * 50)
        logger.info(f"Начало исправления проблем с ботом в {datetime.now()}")
        
        # Проверяем наличие базы данных
        check_database()
        
        # Проверяем наличие миграций
        check_migrations()
        
        # Проверяем наличие тестовых данных
        check_test_data()
        
        # Проверяем наличие файлов бота
        check_bot_files()
        
        # Проверяем наличие переменных окружения
        check_env_variables()
        
        # Создаем отчет о исправлениях
        create_fix_report()
        
        logger.info("Исправление проблем с ботом завершено успешно")
        return True
    
    except Exception as e:
        logger.critical(f"Критическая ошибка при исправлении проблем с ботом: {e}")
        traceback.print_exc()
        return False

def check_database():
    """Проверка наличия базы данных"""
    logger.info("Проверка наличия базы данных...")
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.db")
    
    if not os.path.exists(db_path):
        logger.warning(f"База данных не найдена: {db_path}")
        logger.info("Создание базы данных...")
        
        # Применяем миграции для создания базы данных
        try:
            from apply_migrations import apply_migrations
            apply_migrations()
            logger.info("База данных успешно создана")
        except Exception as e:
            logger.error(f"Ошибка при создании базы данных: {e}")
            raise
    else:
        logger.info(f"База данных найдена: {db_path}")
        
        # Проверяем структуру базы данных
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Получаем список таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            tables = [table[0] for table in tables]
            
            logger.info(f"Найдено {len(tables)} таблиц в базе данных")
            
            # Проверяем наличие основных таблиц
            required_tables = ["users", "categories", "cities", "requests", "distributions"]
            for table in required_tables:
                if table not in tables:
                    logger.warning(f"Таблица '{table}' не найдена в базе данных")
                    raise Exception(f"Таблица '{table}' не найдена в базе данных")
            
            # Проверяем наличие таблицы подкатегорий
            if "subcategories" not in tables:
                logger.warning("Таблица 'subcategories' не найдена в базе данных")
                logger.info("Применение миграции подкатегорий...")
                
                try:
                    from apply_subcategories_migration import apply_migration
                    apply_migration()
                    logger.info("Миграция подкатегорий успешно применена")
                except Exception as e:
                    logger.error(f"Ошибка при применении миграции подкатегорий: {e}")
                    raise
            
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка при проверке структуры базы данных: {e}")
            raise

def check_migrations():
    """Проверка наличия миграций"""
    logger.info("Проверка наличия миграций...")
    
    migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations", "versions")
    
    if not os.path.exists(migrations_dir):
        logger.warning(f"Директория миграций не найдена: {migrations_dir}")
        logger.info("Создание директории миграций...")
        
        try:
            os.makedirs(migrations_dir, exist_ok=True)
            logger.info("Директория миграций успешно создана")
        except Exception as e:
            logger.error(f"Ошибка при создании директории миграций: {e}")
            raise
    else:
        logger.info(f"Директория миграций найдена: {migrations_dir}")
        
        # Проверяем наличие файлов миграций
        migration_files = os.listdir(migrations_dir)
        logger.info(f"Найдено {len(migration_files)} файлов миграций")
        
        # Проверяем наличие миграции подкатегорий
        subcategories_migration_found = False
        for file in migration_files:
            if "add_subcategories" in file:
                subcategories_migration_found = True
                break
        
        if not subcategories_migration_found:
            logger.warning("Миграция подкатегорий не найдена")
            logger.info("Создание миграции подкатегорий...")
            
            try:
                # Копируем файл миграции из репозитория
                subprocess.run(
                    ["curl", "-o", os.path.join(migrations_dir, "add_subcategories.py"),
                     "https://raw.githubusercontent.com/robinso1/botigor2/main/migrations/versions/add_subcategories.py"],
                    check=True
                )
                logger.info("Миграция подкатегорий успешно создана")
            except Exception as e:
                logger.error(f"Ошибка при создании миграции подкатегорий: {e}")
                raise

def check_test_data():
    """Проверка наличия тестовых данных"""
    logger.info("Проверка наличия тестовых данных...")
    
    try:
        # Проверяем наличие категорий и городов
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем наличие категорий
        cursor.execute("SELECT COUNT(*) FROM categories;")
        categories_count = cursor.fetchone()[0]
        logger.info(f"Найдено {categories_count} категорий")
        
        # Проверяем наличие городов
        cursor.execute("SELECT COUNT(*) FROM cities;")
        cities_count = cursor.fetchone()[0]
        logger.info(f"Найдено {cities_count} городов")
        
        # Проверяем наличие подкатегорий
        try:
            cursor.execute("SELECT COUNT(*) FROM subcategories;")
            subcategories_count = cursor.fetchone()[0]
            logger.info(f"Найдено {subcategories_count} подкатегорий")
            
            if subcategories_count == 0:
                logger.warning("Подкатегории не найдены")
                logger.info("Создание тестовых подкатегорий...")
                
                try:
                    from create_test_subcategories import create_test_subcategories
                    create_test_subcategories()
                    logger.info("Тестовые подкатегории успешно созданы")
                except Exception as e:
                    logger.error(f"Ошибка при создании тестовых подкатегорий: {e}")
                    raise
        except sqlite3.OperationalError:
            logger.warning("Таблица 'subcategories' не найдена в базе данных")
            logger.info("Применение миграции подкатегорий...")
            
            try:
                from apply_subcategories_migration import apply_migration
                apply_migration()
                logger.info("Миграция подкатегорий успешно применена")
                
                # Создаем тестовые подкатегории
                from create_test_subcategories import create_test_subcategories
                create_test_subcategories()
                logger.info("Тестовые подкатегории успешно созданы")
            except Exception as e:
                logger.error(f"Ошибка при применении миграции подкатегорий: {e}")
                raise
        
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка при проверке тестовых данных: {e}")
        raise

def check_bot_files():
    """Проверка наличия файлов бота"""
    logger.info("Проверка наличия файлов бота...")
    
    # Проверяем наличие основных файлов
    required_files = [
        "run_bot.py",
        "run_bot_railway.py",
        "run_bot_with_subcategories.py",
        "apply_subcategories_migration.py",
        "create_test_subcategories.py",
        "test_distribution_with_subcategories.py"
    ]
    
    for file in required_files:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
        
        if not os.path.exists(file_path):
            logger.warning(f"Файл '{file}' не найден")
            logger.info(f"Загрузка файла '{file}' из репозитория...")
            
            try:
                # Загружаем файл из репозитория
                subprocess.run(
                    ["curl", "-o", file_path, f"https://raw.githubusercontent.com/robinso1/botigor2/main/{file}"],
                    check=True
                )
                logger.info(f"Файл '{file}' успешно загружен")
            except Exception as e:
                logger.error(f"Ошибка при загрузке файла '{file}': {e}")
                raise
        else:
            logger.info(f"Файл '{file}' найден")

def check_env_variables():
    """Проверка наличия переменных окружения"""
    logger.info("Проверка наличия переменных окружения...")
    
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    
    if not os.path.exists(env_file):
        logger.warning(f"Файл .env не найден: {env_file}")
        logger.info("Создание файла .env...")
        
        try:
            with open(env_file, "w") as f:
                f.write("TELEGRAM_BOT_TOKEN=your_telegram_bot_token\n")
                f.write("ADMIN_IDS=[your_telegram_id]\n")
                f.write("DATABASE_URL=sqlite:///./bot.db\n")
                f.write("SECRET_KEY=your_secret_key\n")
                f.write("DEMO_MODE=True\n")
                f.write("GITHUB_TOKEN=your_github_token\n")
                f.write("GITHUB_REPO=robinso1/botigor2\n")
            
            logger.info("Файл .env успешно создан")
            logger.warning("Необходимо заполнить файл .env корректными значениями")
        except Exception as e:
            logger.error(f"Ошибка при создании файла .env: {e}")
            raise
    else:
        logger.info(f"Файл .env найден: {env_file}")
        
        # Проверяем наличие необходимых переменных
        with open(env_file, "r") as f:
            env_content = f.read()
        
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "ADMIN_IDS",
            "DATABASE_URL",
            "SECRET_KEY",
            "DEMO_MODE"
        ]
        
        for var in required_vars:
            if var not in env_content:
                logger.warning(f"Переменная '{var}' не найдена в файле .env")
                logger.info(f"Добавление переменной '{var}' в файл .env...")
                
                try:
                    with open(env_file, "a") as f:
                        if var == "TELEGRAM_BOT_TOKEN":
                            f.write("TELEGRAM_BOT_TOKEN=your_telegram_bot_token\n")
                        elif var == "ADMIN_IDS":
                            f.write("ADMIN_IDS=[your_telegram_id]\n")
                        elif var == "DATABASE_URL":
                            f.write("DATABASE_URL=sqlite:///./bot.db\n")
                        elif var == "SECRET_KEY":
                            f.write("SECRET_KEY=your_secret_key\n")
                        elif var == "DEMO_MODE":
                            f.write("DEMO_MODE=True\n")
                    
                    logger.info(f"Переменная '{var}' успешно добавлена в файл .env")
                    logger.warning(f"Необходимо заполнить переменную '{var}' корректным значением")
                except Exception as e:
                    logger.error(f"Ошибка при добавлении переменной '{var}' в файл .env: {e}")
                    raise

def create_fix_report():
    """Создание отчета о исправлениях"""
    logger.info("Создание отчета о исправлениях...")
    
    report_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_report.md")
    
    with open(report_file, "w") as f:
        f.write("# Отчет о исправлении проблем с ботом\n\n")
        f.write(f"Дата исправления: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Выполненные проверки\n\n")
        f.write("1. Проверка наличия базы данных\n")
        f.write("2. Проверка наличия миграций\n")
        f.write("3. Проверка наличия тестовых данных\n")
        f.write("4. Проверка наличия файлов бота\n")
        f.write("5. Проверка наличия переменных окружения\n\n")
        
        f.write("## Инструкция по запуску бота\n\n")
        f.write("1. Убедитесь, что все проблемы исправлены\n")
        f.write("2. Запустите бота с помощью команды:\n")
        f.write("```bash\npython run_bot_with_subcategories.py\n```\n\n")
        
        f.write("## Рекомендации\n\n")
        f.write("1. Перед запуском бота убедитесь, что в файле `.env` указан корректный токен бота\n")
        f.write("2. Для тестирования функциональности бота используйте скрипт `test_bot_functionality.py`\n")
        f.write("3. Для тестирования распределения заявок с учетом подкатегорий используйте скрипт `test_distribution_with_subcategories.py`\n")
    
    logger.info(f"Отчет о исправлениях создан: {report_file}")

if __name__ == "__main__":
    logger.info("Запуск скрипта исправления проблем с ботом")
    
    try:
        # Запускаем исправление проблем
        if fix_bot_issues():
            logger.info("Скрипт успешно выполнен")
            print("\n" + "=" * 50)
            print("Исправление проблем с ботом завершено успешно!")
            print("Для запуска бота выполните команду:")
            print("python run_bot_with_subcategories.py")
            print("=" * 50 + "\n")
            sys.exit(0)
        else:
            logger.error("Ошибка при исправлении проблем с ботом")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Исправление проблем остановлено пользователем (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        traceback.print_exc()
        sys.exit(1) 