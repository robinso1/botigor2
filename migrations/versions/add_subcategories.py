"""
Миграция для добавления подкатегорий
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Идентификатор ревизии
revision = 'add_subcategories'
# Идентификатор предыдущей ревизии
down_revision = 'add_expires_at_column'
# Дата создания
create_date = '2023-06-15 12:00:00.000000'

def upgrade():
    """
    Обновление схемы базы данных:
    1. Создание таблицы подкатегорий
    2. Создание таблицы связи пользователей и подкатегорий
    3. Создание таблицы связи заявок и подкатегорий
    4. Добавление полей для дополнительных критериев в таблицу заявок
    """
    # Создаем таблицу подкатегорий
    op.create_table(
        'subcategories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создаем таблицу связи пользователей и подкатегорий
    op.create_table(
        'user_subcategory',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subcategory_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['subcategory_id'], ['subcategories.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'subcategory_id')
    )
    
    # Создаем таблицу связи заявок и подкатегорий
    op.create_table(
        'request_subcategory',
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('subcategory_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ),
        sa.ForeignKeyConstraint(['subcategory_id'], ['subcategories.id'], ),
        sa.PrimaryKeyConstraint('request_id', 'subcategory_id')
    )
    
    # Добавляем поля для дополнительных критериев в таблицу заявок
    op.add_column('requests', sa.Column('area_value', sa.Float(), nullable=True))
    op.add_column('requests', sa.Column('house_type', sa.String(length=100), nullable=True))
    op.add_column('requests', sa.Column('has_design_project', sa.Boolean(), nullable=True))

def downgrade():
    """
    Откат изменений:
    1. Удаление полей для дополнительных критериев из таблицы заявок
    2. Удаление таблицы связи заявок и подкатегорий
    3. Удаление таблицы связи пользователей и подкатегорий
    4. Удаление таблицы подкатегорий
    """
    # Удаляем поля для дополнительных критериев из таблицы заявок
    op.drop_column('requests', 'has_design_project')
    op.drop_column('requests', 'house_type')
    op.drop_column('requests', 'area_value')
    
    # Удаляем таблицу связи заявок и подкатегорий
    op.drop_table('request_subcategory')
    
    # Удаляем таблицу связи пользователей и подкатегорий
    op.drop_table('user_subcategory')
    
    # Удаляем таблицу подкатегорий
    op.drop_table('subcategories') 