"""add sector category to index ohlcv

Revision ID: abc123456789
Revises: 6ba5b534906f
Create Date: 2025-12-26 15:05:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc123456789'
down_revision = '6ba5b534906f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add sector_category column to index_ohlcv_daily table
    op.add_column('index_ohlcv_daily',
        sa.Column('sector_category', sa.String(length=50), nullable=True,
                 comment="Sector category (e.g., Banking, IT, Pharma, Auto, etc.)"))

    op.add_column('index_ohlcv_daily',
        sa.Column('is_sectoral', sa.Boolean(), nullable=True, server_default='false',
                 comment="True if sectoral/thematic index, False for broad market indices"))

    # Add index for filtering by sector
    op.create_index('idx_index_ohlcv_sector', 'index_ohlcv_daily', ['sector_category'])


def downgrade() -> None:
    op.drop_index('idx_index_ohlcv_sector', table_name='index_ohlcv_daily')
    op.drop_column('index_ohlcv_daily', 'is_sectoral')
    op.drop_column('index_ohlcv_daily', 'sector_category')
