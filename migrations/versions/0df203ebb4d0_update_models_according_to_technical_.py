"""Update models according to technical requirements

Revision ID: 0df203ebb4d0
Revises: 9872f9eac55a
Create Date: 2025-03-04 20:05:17.825427

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '0df203ebb4d0'
down_revision = '9872f9eac55a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Create new tables
    op.create_table('service_packages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('services', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user_statistics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('total_requests', sa.Integer(), nullable=True),
    sa.Column('processed_requests', sa.Integer(), nullable=True),
    sa.Column('successful_requests', sa.Integer(), nullable=True),
    sa.Column('avg_response_time', sa.Float(), nullable=True),
    sa.Column('conversion_rate', sa.Float(), nullable=True),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('request_package',
    sa.Column('request_id', sa.Integer(), nullable=False),
    sa.Column('package_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['package_id'], ['service_packages.id'], ),
    sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ),
    sa.PrimaryKeyConstraint('request_id', 'package_id')
    )
    
    # Add simple columns to existing tables
    op.add_column('distributions', sa.Column('response_time', sa.Integer(), nullable=True))
    op.add_column('distributions', sa.Column('is_converted', sa.Boolean(), nullable=True))
    op.add_column('requests', sa.Column('estimated_cost', sa.Float(), nullable=True))
    op.add_column('requests', sa.Column('crm_id', sa.String(length=100), nullable=True))
    op.add_column('requests', sa.Column('crm_status', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('rating', sa.Float(), nullable=True))
    
    # Add parent_id to categories using batch operations
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_categories_parent_id', 'categories', ['parent_id'], ['id'])
    
    # Convert status column in requests to enum using batch operations
    # First, create a temporary table with the new schema
    conn = op.get_bind()
    conn.execute(sa.text('''
        CREATE TABLE requests_new (
            id INTEGER NOT NULL, 
            source_chat_id INTEGER, 
            source_message_id INTEGER, 
            client_name VARCHAR(100), 
            client_phone VARCHAR(20), 
            description TEXT, 
            status VARCHAR(50), 
            area FLOAT, 
            address VARCHAR(255), 
            is_demo BOOLEAN, 
            created_at DATETIME, 
            updated_at DATETIME, 
            category_id INTEGER, 
            city_id INTEGER, 
            extra_data JSON,
            estimated_cost FLOAT,
            crm_id VARCHAR(100),
            crm_status VARCHAR(50),
            PRIMARY KEY (id), 
            FOREIGN KEY(category_id) REFERENCES categories (id), 
            FOREIGN KEY(city_id) REFERENCES cities (id)
        )
    '''))
    
    # Copy data from old table to new table
    conn.execute(sa.text('''
        INSERT INTO requests_new 
        SELECT id, source_chat_id, source_message_id, client_name, client_phone, 
               description, status, area, address, is_demo, created_at, updated_at, 
               category_id, city_id, extra_data, estimated_cost, crm_id, crm_status
        FROM requests
    '''))
    
    # Drop old table and rename new table
    conn.execute(sa.text('DROP TABLE requests'))
    conn.execute(sa.text('ALTER TABLE requests_new RENAME TO requests'))
    
    # Recreate indexes and foreign keys
    conn.execute(sa.text('''
        CREATE INDEX ix_requests_category_id ON requests (category_id)
    '''))
    conn.execute(sa.text('''
        CREATE INDEX ix_requests_city_id ON requests (city_id)
    '''))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Drop columns from users
    op.drop_column('users', 'rating')
    
    # Drop columns from requests
    op.drop_column('requests', 'crm_status')
    op.drop_column('requests', 'crm_id')
    op.drop_column('requests', 'estimated_cost')
    
    # Drop columns from distributions
    op.drop_column('distributions', 'is_converted')
    op.drop_column('distributions', 'response_time')
    
    # Remove parent_id from categories using batch operations
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_constraint('fk_categories_parent_id', type_='foreignkey')
        batch_op.drop_column('parent_id')
    
    # Drop tables
    op.drop_table('request_package')
    op.drop_table('user_statistics')
    op.drop_table('service_packages')
    # ### end Alembic commands ### 