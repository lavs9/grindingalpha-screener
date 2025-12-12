"""add_ingestion_logs_table

Revision ID: e9dd4cc896bc
Revises: 1832bc1d8bcd
Create Date: 2025-12-12 07:15:47.491708

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9dd4cc896bc'
down_revision = '1832bc1d8bcd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ingestion_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('records_fetched', sa.Integer(), nullable=True),
        sa.Column('records_inserted', sa.Integer(), nullable=True),
        sa.Column('records_updated', sa.Integer(), nullable=True),
        sa.Column('records_failed', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ingestion_logs_source_timestamp', 'ingestion_logs', ['source', 'timestamp'], unique=False)
    op.create_index('idx_ingestion_logs_timestamp', 'ingestion_logs', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_ingestion_logs_timestamp', table_name='ingestion_logs')
    op.drop_index('idx_ingestion_logs_source_timestamp', table_name='ingestion_logs')
    op.drop_table('ingestion_logs')
