import os
import sys
import subprocess

def apply_migrations():
    """Применяет миграции базы данных"""
    try:
        # Запускаем команду alembic для применения миграций
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Миграции успешно применены")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при применении миграций: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_migrations() 