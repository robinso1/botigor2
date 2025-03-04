"""Add missing columns to tables

Revision ID: add_missing_columns
Revises: 0df203ebb4d0
Create Date: 2023-03-04 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_missing_columns'
down_revision = '0df203ebb4d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем колонку rating в таблицу users
    op.add_column('users', sa.Column('rating', sa.Float(), server_default=sa.text('0.0')))
    
    # Добавляем колонки response_time и is_converted в таблицу distributions
    op.add_column('distributions', sa.Column('response_time', sa.Integer(), nullable=True))
    op.add_column('distributions', sa.Column('is_converted', sa.Boolean(), server_default=sa.text('0')))


def downgrade() -> None:
    # Удаляем колонки
    op.drop_column('users', 'rating')
    op.drop_column('distributions', 'response_time')
    op.drop_column('distributions', 'is_converted') 