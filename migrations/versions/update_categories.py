"""Update categories structure

Revision ID: update_categories
Revises: add_missing_columns
Create Date: 2025-03-04 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'update_categories'
down_revision = 'add_missing_columns'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Очищаем существующие связи
    op.execute("DELETE FROM user_category")
    
    # Очищаем существующие категории
    op.execute("DELETE FROM categories")
    
    # Добавляем новые категории
    categories = [
        {"id": 1, "name": "Натяжные потолки", "description": "Установка и обслуживание натяжных потолков", "is_active": True, "parent_id": None},
        {"id": 2, "name": "Сантехника", "description": "Сантехнические работы любой сложности", "is_active": True, "parent_id": None},
        {"id": 3, "name": "Электрика", "description": "Электромонтажные работы", "is_active": True, "parent_id": None},
        {"id": 4, "name": "Дизайн интерьера", "description": "Разработка дизайн-проектов помещений", "is_active": True, "parent_id": None},
        {"id": 5, "name": "Кухни на заказ", "description": "Изготовление и установка кухонь", "is_active": True, "parent_id": None},
        {"id": 6, "name": "Строительство каркасных домов", "description": "Строительство каркасных домов под ключ", "is_active": True, "parent_id": None},
        {"id": 7, "name": "Строительство блочных домов", "description": "Строительство домов из блоков под ключ", "is_active": True, "parent_id": None},
    ]
    
    for category in categories:
        op.execute(
            "INSERT INTO categories (id, name, description, is_active, parent_id) VALUES "
            f"({category['id']}, '{category['name']}', '{category['description']}', {1 if category['is_active'] else 0}, "
            f"{category['parent_id'] if category['parent_id'] is not None else 'NULL'})"
        )

def downgrade() -> None:
    # При откате просто очищаем таблицу категорий
    op.execute('DELETE FROM user_category')
    op.execute('DELETE FROM requests WHERE category_id IS NOT NULL')
    op.execute('DELETE FROM categories') 