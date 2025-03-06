"""Add subcategories and additional criteria

Revision ID: add_subcategories
Revises: add_expires_at_column
Create Date: 2025-03-06 22:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_subcategories'
down_revision = 'add_expires_at_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем таблицу подкатегорий
    op.create_table(
        'subcategories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
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
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ),
        sa.ForeignKeyConstraint(['subcategory_id'], ['subcategories.id'], ),
        sa.PrimaryKeyConstraint('request_id', 'subcategory_id')
    )
    
    # Добавляем поля для подкатегорий в таблицу requests
    op.add_column('requests', sa.Column('area_value', sa.Float(), nullable=True))
    op.add_column('requests', sa.Column('house_type', sa.String(length=50), nullable=True))
    op.add_column('requests', sa.Column('has_design_project', sa.Boolean(), nullable=True))


def downgrade() -> None:
    # Удаляем поля из таблицы requests
    op.drop_column('requests', 'has_design_project')
    op.drop_column('requests', 'house_type')
    op.drop_column('requests', 'area_value')
    
    # Удаляем таблицы
    op.drop_table('request_subcategory')
    op.drop_table('user_subcategory')
    op.drop_table('subcategories') 