"""create_index_ohlcv_table

Revision ID: 6ba5b534906f
Revises: 8ba3cfea4bbe
Create Date: 2025-12-26 04:25:56.406703

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ba5b534906f'
down_revision = '8ba3cfea4bbe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create index_ohlcv_daily table for storing NSE index OHLCV data
    op.create_table(
        'index_ohlcv_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False, comment='Index symbol (e.g., NIFTY 50, NIFTY BANK)'),
        sa.Column('date', sa.Date(), nullable=False, comment='Trading date'),
        sa.Column('open', sa.Numeric(precision=12, scale=2), nullable=False, comment='Opening index value'),
        sa.Column('high', sa.Numeric(precision=12, scale=2), nullable=False, comment='Highest index value'),
        sa.Column('low', sa.Numeric(precision=12, scale=2), nullable=False, comment='Lowest index value'),
        sa.Column('close', sa.Numeric(precision=12, scale=2), nullable=False, comment='Closing index value'),
        sa.Column('volume', sa.BigInteger(), nullable=True, comment='Volume (may be null for some indices)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'date', name='uq_index_ohlcv_symbol_date'),
        comment='Daily OHLCV data for NSE indices (NIFTY 50, sectoral indices, etc.)'
    )

    # Create indexes for faster queries
    op.create_index('idx_index_ohlcv_symbol_date_desc', 'index_ohlcv_daily', ['symbol', sa.text('date DESC')])
    op.create_index('idx_index_ohlcv_date', 'index_ohlcv_daily', ['date'])


def downgrade() -> None:
    op.drop_index('idx_index_ohlcv_date', table_name='index_ohlcv_daily')
    op.drop_index('idx_index_ohlcv_symbol_date_desc', table_name='index_ohlcv_daily')
    op.drop_table('index_ohlcv_daily')
