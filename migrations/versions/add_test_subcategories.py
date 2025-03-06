"""Добавление тестовых подкатегорий

Revision ID: add_test_subcategories
Revises: add_subcategories
Create Date: 2023-10-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Float, Boolean, Text


# revision identifiers, used by Alembic.
revision = 'add_test_subcategories'
down_revision = 'add_subcategories'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем временные таблицы для вставки данных
    subcategories = table('subcategories',
        column('id', Integer),
        column('name', String),
        column('description', Text),
        column('category_id', Integer),
        column('type', String),
        column('min_value', Float),
        column('max_value', Float),
        column('is_active', Boolean)
    )
    
    # Получаем ID категорий (предполагаем, что категории "Ремонт" и "Строительство" уже существуют)
    # В реальном сценарии нужно проверить фактические ID
    repair_category_id = 1  # ID категории "Ремонт"
    construction_category_id = 2  # ID категории "Строительство"
    
    # Добавляем подкатегории для типа дома
    op.bulk_insert(subcategories, [
        {
            'name': 'Панельный дом',
            'description': 'Ремонт в панельном доме',
            'category_id': repair_category_id,
            'type': 'house_type',
            'min_value': None,
            'max_value': None,
            'is_active': True
        },
        {
            'name': 'Кирпичный дом',
            'description': 'Ремонт в кирпичном доме',
            'category_id': repair_category_id,
            'type': 'house_type',
            'min_value': None,
            'max_value': None,
            'is_active': True
        },
        {
            'name': 'Монолитный дом',
            'description': 'Ремонт в монолитном доме',
            'category_id': repair_category_id,
            'type': 'house_type',
            'min_value': None,
            'max_value': None,
            'is_active': True
        },
        {
            'name': 'Деревянный дом',
            'description': 'Ремонт в деревянном доме',
            'category_id': repair_category_id,
            'type': 'house_type',
            'min_value': None,
            'max_value': None,
            'is_active': True
        }
    ])
    
    # Добавляем подкатегории для наличия дизайн-проекта
    op.bulk_insert(subcategories, [
        {
            'name': 'С дизайн-проектом',
            'description': 'Ремонт с готовым дизайн-проектом',
            'category_id': repair_category_id,
            'type': 'design_project',
            'min_value': None,
            'max_value': None,
            'is_active': True
        },
        {
            'name': 'Без дизайн-проекта',
            'description': 'Ремонт без дизайн-проекта',
            'category_id': repair_category_id,
            'type': 'design_project',
            'min_value': None,
            'max_value': None,
            'is_active': True
        }
    ])
    
    # Добавляем подкатегории для площади
    op.bulk_insert(subcategories, [
        {
            'name': 'До 50 м²',
            'description': 'Площадь до 50 квадратных метров',
            'category_id': repair_category_id,
            'type': 'area',
            'min_value': 0,
            'max_value': 50,
            'is_active': True
        },
        {
            'name': '50-100 м²',
            'description': 'Площадь от 50 до 100 квадратных метров',
            'category_id': repair_category_id,
            'type': 'area',
            'min_value': 50,
            'max_value': 100,
            'is_active': True
        },
        {
            'name': '100-200 м²',
            'description': 'Площадь от 100 до 200 квадратных метров',
            'category_id': repair_category_id,
            'type': 'area',
            'min_value': 100,
            'max_value': 200,
            'is_active': True
        },
        {
            'name': 'Более 200 м²',
            'description': 'Площадь более 200 квадратных метров',
            'category_id': repair_category_id,
            'type': 'area',
            'min_value': 200,
            'max_value': None,
            'is_active': True
        }
    ])
    
    # Добавляем аналогичные подкатегории для строительства
    op.bulk_insert(subcategories, [
        {
            'name': 'Каркасный дом',
            'description': 'Строительство каркасного дома',
            'category_id': construction_category_id,
            'type': 'house_type',
            'min_value': None,
            'max_value': None,
            'is_active': True
        },
        {
            'name': 'Кирпичный дом',
            'description': 'Строительство кирпичного дома',
            'category_id': construction_category_id,
            'type': 'house_type',
            'min_value': None,
            'max_value': None,
            'is_active': True
        },
        {
            'name': 'Деревянный дом',
            'description': 'Строительство деревянного дома',
            'category_id': construction_category_id,
            'type': 'house_type',
            'min_value': None,
            'max_value': None,
            'is_active': True
        },
        {
            'name': 'С дизайн-проектом',
            'description': 'Строительство с готовым дизайн-проектом',
            'category_id': construction_category_id,
            'type': 'design_project',
            'min_value': None,
            'max_value': None,
            'is_active': True
        },
        {
            'name': 'Без дизайн-проекта',
            'description': 'Строительство без дизайн-проекта',
            'category_id': construction_category_id,
            'type': 'design_project',
            'min_value': None,
            'max_value': None,
            'is_active': True
        }
    ])


def downgrade() -> None:
    # Удаляем все добавленные подкатегории
    op.execute("DELETE FROM subcategories WHERE type IN ('house_type', 'design_project', 'area')") 