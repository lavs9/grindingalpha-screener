"""Add technical indicators: RSI, MACD, Bollinger Bands, ADX

Revision ID: d4f2a8b9c7e1
Revises: 6ba5b534906f
Create Date: 2025-12-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4f2a8b9c7e1'
down_revision = '6ba5b534906f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # RSI Indicator (3 columns)
    op.add_column('calculated_metrics', sa.Column('rsi_14', sa.Numeric(precision=10, scale=4), nullable=True, comment='14-period RSI (Wilder smoothing)'))
    op.add_column('calculated_metrics', sa.Column('rsi_oversold', sa.Integer(), nullable=True, comment='1 if RSI < 30, else 0'))
    op.add_column('calculated_metrics', sa.Column('rsi_overbought', sa.Integer(), nullable=True, comment='1 if RSI > 70, else 0'))

    # MACD Indicator (5 columns)
    op.add_column('calculated_metrics', sa.Column('macd_line', sa.Numeric(precision=10, scale=4), nullable=True, comment='12-EMA - 26-EMA'))
    op.add_column('calculated_metrics', sa.Column('macd_signal', sa.Numeric(precision=10, scale=4), nullable=True, comment='9-EMA of MACD line'))
    op.add_column('calculated_metrics', sa.Column('macd_histogram', sa.Numeric(precision=10, scale=4), nullable=True, comment='MACD line - Signal line'))
    op.add_column('calculated_metrics', sa.Column('is_macd_bullish_cross', sa.Integer(), nullable=True, comment='1 if MACD line crossed above signal today, else 0'))
    op.add_column('calculated_metrics', sa.Column('is_macd_bearish_cross', sa.Integer(), nullable=True, comment='1 if MACD line crossed below signal today, else 0'))

    # Bollinger Bands (5 columns)
    op.add_column('calculated_metrics', sa.Column('bb_upper', sa.Numeric(precision=15, scale=4), nullable=True, comment='20-SMA + 2*stddev'))
    op.add_column('calculated_metrics', sa.Column('bb_middle', sa.Numeric(precision=15, scale=4), nullable=True, comment='20-SMA'))
    op.add_column('calculated_metrics', sa.Column('bb_lower', sa.Numeric(precision=15, scale=4), nullable=True, comment='20-SMA - 2*stddev'))
    op.add_column('calculated_metrics', sa.Column('bb_bandwidth_percent', sa.Numeric(precision=10, scale=4), nullable=True, comment='(Upper-Lower)/Middle * 100'))
    op.add_column('calculated_metrics', sa.Column('is_bb_squeeze', sa.Integer(), nullable=True, comment='1 if Bandwidth < 10%, else 0'))

    # ADX Trend Strength (4 columns)
    op.add_column('calculated_metrics', sa.Column('adx_14', sa.Numeric(precision=10, scale=4), nullable=True, comment='14-period ADX (Average Directional Index)'))
    op.add_column('calculated_metrics', sa.Column('di_plus', sa.Numeric(precision=10, scale=4), nullable=True, comment='14-period +DI (Plus Directional Indicator)'))
    op.add_column('calculated_metrics', sa.Column('di_minus', sa.Numeric(precision=10, scale=4), nullable=True, comment='14-period -DI (Minus Directional Indicator)'))
    op.add_column('calculated_metrics', sa.Column('is_strong_trend', sa.Integer(), nullable=True, comment='1 if ADX > 25, else 0'))

    # Create indexes for new columns (optimized for screener queries)
    op.create_index('idx_metrics_rsi_14', 'calculated_metrics', ['rsi_14'], unique=False)
    op.create_index('idx_metrics_macd_histogram', 'calculated_metrics', ['macd_histogram'], unique=False)
    op.create_index('idx_metrics_bb_bandwidth', 'calculated_metrics', ['bb_bandwidth_percent'], unique=False)
    op.create_index('idx_metrics_adx_14', 'calculated_metrics', ['adx_14'], unique=False)
    op.create_index('idx_metrics_is_bb_squeeze', 'calculated_metrics', ['is_bb_squeeze', 'date'], unique=False)
    op.create_index('idx_metrics_is_strong_trend', 'calculated_metrics', ['is_strong_trend', 'date'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_metrics_is_strong_trend', table_name='calculated_metrics')
    op.drop_index('idx_metrics_is_bb_squeeze', table_name='calculated_metrics')
    op.drop_index('idx_metrics_adx_14', table_name='calculated_metrics')
    op.drop_index('idx_metrics_bb_bandwidth', table_name='calculated_metrics')
    op.drop_index('idx_metrics_macd_histogram', table_name='calculated_metrics')
    op.drop_index('idx_metrics_rsi_14', table_name='calculated_metrics')

    # Drop ADX columns
    op.drop_column('calculated_metrics', 'is_strong_trend')
    op.drop_column('calculated_metrics', 'di_minus')
    op.drop_column('calculated_metrics', 'di_plus')
    op.drop_column('calculated_metrics', 'adx_14')

    # Drop Bollinger Bands columns
    op.drop_column('calculated_metrics', 'is_bb_squeeze')
    op.drop_column('calculated_metrics', 'bb_bandwidth_percent')
    op.drop_column('calculated_metrics', 'bb_lower')
    op.drop_column('calculated_metrics', 'bb_middle')
    op.drop_column('calculated_metrics', 'bb_upper')

    # Drop MACD columns
    op.drop_column('calculated_metrics', 'is_macd_bearish_cross')
    op.drop_column('calculated_metrics', 'is_macd_bullish_cross')
    op.drop_column('calculated_metrics', 'macd_histogram')
    op.drop_column('calculated_metrics', 'macd_signal')
    op.drop_column('calculated_metrics', 'macd_line')

    # Drop RSI columns
    op.drop_column('calculated_metrics', 'rsi_overbought')
    op.drop_column('calculated_metrics', 'rsi_oversold')
    op.drop_column('calculated_metrics', 'rsi_14')
