import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
root_dir = Path(__file__).parent.absolute()
sys.path.append(str(root_dir))

from alembic.config import Config
from alembic import command

def run_migrations():
    """Запуск миграций базы данных"""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    run_migrations() 