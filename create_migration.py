import os
import sys
import subprocess
from datetime import datetime

def create_migration():
    """Создает миграцию базы данных"""
    # Получаем текущую дату и время для имени миграции
    now = datetime.now()
    migration_name = f"migration_{now.strftime('%Y%m%d_%H%M%S')}"
    
    # Запускаем команду alembic для создания миграции
    try:
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", migration_name], check=True)
        print(f"Миграция {migration_name} успешно создана")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании миграции: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_migration() 