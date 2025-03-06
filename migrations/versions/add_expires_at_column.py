"""Add expires_at column to distributions table

Revision ID: add_expires_at_column
Revises: update_categories
Create Date: 2025-03-06 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_expires_at_column'
down_revision = 'update_categories'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем колонку expires_at в таблицу distributions
    op.add_column('distributions', sa.Column('expires_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Удаляем колонку expires_at из таблицы distributions
    op.drop_column('distributions', 'expires_at') 