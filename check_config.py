"""
Скрипт для проверки конфигурации и переменных окружения
"""
import os
import sys
import json
from dotenv import load_dotenv

def check_env_file():
    """Проверяет наличие файла .env"""
    if not os.path.exists('.env'):
        print("ОШИБКА: Файл .env не найден")
        print("Создайте файл .env с необходимыми переменными окружения")
        return False
    return True

def check_required_vars():
    """Проверяет наличие необходимых переменных окружения"""
    load_dotenv()
    
    required_vars = {
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "ADMIN_IDS": os.getenv("ADMIN_IDS"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "SECRET_KEY": os.getenv("SECRET_KEY")
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        print(f"ОШИБКА: Отсутствуют следующие переменные окружения: {', '.join(missing_vars)}")
        return False
    
    return True

def check_admin_ids():
    """Проверяет корректность формата ADMIN_IDS"""
    admin_ids_str = os.getenv("ADMIN_IDS", "[]")
    
    try:
        admin_ids = json.loads(admin_ids_str)
        if not isinstance(admin_ids, list):
            print("ОШИБКА: ADMIN_IDS должен быть списком")
            return False
        
        if not admin_ids:
            print("ПРЕДУПРЕЖДЕНИЕ: Список ADMIN_IDS пуст. Никто не сможет использовать административные функции.")
        else:
            print(f"Администраторы: {admin_ids}")
        
        return True
    except json.JSONDecodeError:
        print("ОШИБКА: ADMIN_IDS имеет неверный формат JSON")
        return False

def check_database():
    """Проверяет доступность базы данных"""
    from sqlalchemy import create_engine
    from sqlalchemy.exc import SQLAlchemyError
    
    database_url = os.getenv("DATABASE_URL", "sqlite:///./bot.db")
    
    try:
        engine = create_engine(database_url)
        connection = engine.connect()
        connection.close()
        print(f"База данных доступна: {database_url}")
        return True
    except SQLAlchemyError as e:
        print(f"ОШИБКА: Не удалось подключиться к базе данных: {e}")
        return False

def check_demo_mode():
    """Проверяет настройки демо-режима"""
    demo_mode = os.getenv("DEMO_MODE", "False").lower() in ("true", "1", "t")
    
    if demo_mode:
        print("Демо-режим ВКЛЮЧЕН. Будут генерироваться тестовые заявки.")
    else:
        print("Демо-режим ВЫКЛЮЧЕН.")
    
    return True

def main():
    """Основная функция скрипта"""
    print("=" * 50)
    print("Проверка конфигурации и переменных окружения")
    print("=" * 50)
    
    checks = [
        ("Проверка файла .env", check_env_file),
        ("Проверка необходимых переменных", check_required_vars),
        ("Проверка списка администраторов", check_admin_ids),
        ("Проверка базы данных", check_database),
        ("Проверка демо-режима", check_demo_mode)
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        print(f"\n{name}...")
        try:
            result = check_func()
            if not result:
                all_passed = False
                print(f"✗ {name} НЕ ПРОЙДЕНА")
            else:
                print(f"✓ {name} ПРОЙДЕНА")
        except Exception as e:
            all_passed = False
            print(f"✗ {name} ВЫЗВАЛА ОШИБКУ: {e}")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ Все проверки пройдены успешно!")
        return 0
    else:
        print("✗ Некоторые проверки не пройдены. Исправьте ошибки перед запуском бота.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 