"""Add missing columns to tables

Revision ID: add_missing_columns
Revises: 0df203ebb4d0
Create Date: 2023-03-04 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'add_missing_columns'
down_revision = '0df203ebb4d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Получаем инспектор для проверки существования колонок
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Проверяем и добавляем колонку rating в таблицу users
    users_columns = [column['name'] for column in inspector.get_columns('users')]
    if 'rating' not in users_columns:
        op.add_column('users', sa.Column('rating', sa.Float(), server_default=sa.text('0.0')))
    
    # Проверяем и добавляем колонки response_time и is_converted в таблицу distributions
    distributions_columns = [column['name'] for column in inspector.get_columns('distributions')]
    if 'response_time' not in distributions_columns:
        op.add_column('distributions', sa.Column('response_time', sa.Integer(), nullable=True))
    if 'is_converted' not in distributions_columns:
        op.add_column('distributions', sa.Column('is_converted', sa.Boolean(), server_default=sa.text('0')))


def downgrade() -> None:
    # Удаляем колонки
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    users_columns = [column['name'] for column in inspector.get_columns('users')]
    if 'rating' in users_columns:
        op.drop_column('users', 'rating')
    
    distributions_columns = [column['name'] for column in inspector.get_columns('distributions')]
    if 'response_time' in distributions_columns:
        op.drop_column('distributions', 'response_time')
    if 'is_converted' in distributions_columns:
        op.drop_column('distributions', 'is_converted') 