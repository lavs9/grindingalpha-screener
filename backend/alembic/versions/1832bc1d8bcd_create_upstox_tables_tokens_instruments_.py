"""Create Upstox tables (tokens, instruments, mappings)

Revision ID: 1832bc1d8bcd
Revises: 725e3b233476
Create Date: 2025-11-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1832bc1d8bcd'
down_revision = '725e3b233476'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create upstox_tokens table
    op.create_table('upstox_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False, comment='JWT access token for API calls'),
        sa.Column('refresh_token', sa.Text(), nullable=True, comment='Refresh token for token renewal (can be NULL if using API key auth)'),
        sa.Column('token_type', sa.String(length=20), nullable=True, server_default='Bearer', comment='Token type (always \'Bearer\' for OAuth2)'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='Token expiration timestamp (typically 23:59 IST)'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true', comment='Whether token is currently valid and usable'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True, comment='Last time this token was used for API calls'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='Token issuance timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='Last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('access_token')
    )
    op.create_index('idx_upstox_tokens_active_expires', 'upstox_tokens', ['is_active', 'expires_at'], unique=False)
    op.create_index(op.f('ix_upstox_tokens_is_active'), 'upstox_tokens', ['is_active'], unique=False)

    # Create upstox_instruments table
    op.create_table('upstox_instruments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('instrument_key', sa.String(length=50), nullable=False, comment='Unique Upstox instrument identifier (e.g., \'NSE_EQ|INE002A01018\')'),
        sa.Column('exchange', sa.String(length=20), nullable=False, comment='Exchange (NSE, BSE, NFO, MCX, etc.)'),
        sa.Column('symbol', sa.String(length=50), nullable=False, comment='NSE/BSE trading symbol (e.g., \'RELIANCE\')'),
        sa.Column('isin', sa.String(length=12), nullable=True, comment='12-character ISIN code'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Full instrument name from Upstox'),
        sa.Column('instrument_type', sa.String(length=50), nullable=True, comment='Instrument type (EQUITY, INDEX, DERIVATIVE, etc.)'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true', comment='Whether instrument is actively traded'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='Last sync from Upstox API'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('instrument_key'),
        sa.UniqueConstraint('exchange', 'symbol', name='uq_upstox_exchange_symbol')
    )
    op.create_index('idx_upstox_instr_symbol_exchange', 'upstox_instruments', ['symbol', 'exchange'], unique=False)
    op.create_index(op.f('ix_upstox_instruments_exchange'), 'upstox_instruments', ['exchange'], unique=False)
    op.create_index(op.f('ix_upstox_instruments_instrument_key'), 'upstox_instruments', ['instrument_key'], unique=False)
    op.create_index(op.f('ix_upstox_instruments_is_active'), 'upstox_instruments', ['is_active'], unique=False)
    op.create_index(op.f('ix_upstox_instruments_isin'), 'upstox_instruments', ['isin'], unique=False)
    op.create_index(op.f('ix_upstox_instruments_symbol'), 'upstox_instruments', ['symbol'], unique=False)

    # Create symbol_instrument_mapping table
    op.create_table('symbol_instrument_mapping',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('security_id', sa.Integer(), nullable=False, comment='FK to securities table'),
        sa.Column('instrument_id', sa.Integer(), nullable=False, comment='FK to upstox_instruments table'),
        sa.Column('symbol', sa.String(length=50), nullable=False, comment='NSE symbol (denormalized from securities.symbol)'),
        sa.Column('instrument_key', sa.String(length=50), nullable=False, comment='Upstox instrument_key (denormalized from upstox_instruments)'),
        sa.Column('is_primary', sa.Boolean(), nullable=True, server_default='true', comment='Whether this is the primary mapping for this symbol'),
        sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=True, server_default='100', comment='Confidence score (0-100) for mapping accuracy'),
        sa.Column('match_method', sa.String(length=50), nullable=True, comment='How mapping was created (auto_isin, auto_symbol, manual)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['security_id'], ['securities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instrument_id'], ['upstox_instruments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('security_id', 'instrument_id', name='uq_mapping_security_instrument')
    )
    op.create_index('idx_mapping_symbol_instrument', 'symbol_instrument_mapping', ['symbol', 'instrument_key'], unique=False)
    op.create_index(op.f('ix_symbol_instrument_mapping_instrument_id'), 'symbol_instrument_mapping', ['instrument_id'], unique=False)
    op.create_index(op.f('ix_symbol_instrument_mapping_security_id'), 'symbol_instrument_mapping', ['security_id'], unique=False)
    op.create_index(op.f('ix_symbol_instrument_mapping_symbol'), 'symbol_instrument_mapping', ['symbol'], unique=False)


def downgrade() -> None:
    # Drop symbol_instrument_mapping table
    op.drop_index(op.f('ix_symbol_instrument_mapping_symbol'), table_name='symbol_instrument_mapping')
    op.drop_index(op.f('ix_symbol_instrument_mapping_security_id'), table_name='symbol_instrument_mapping')
    op.drop_index(op.f('ix_symbol_instrument_mapping_instrument_id'), table_name='symbol_instrument_mapping')
    op.drop_index('idx_mapping_symbol_instrument', table_name='symbol_instrument_mapping')
    op.drop_table('symbol_instrument_mapping')

    # Drop upstox_instruments table
    op.drop_index(op.f('ix_upstox_instruments_symbol'), table_name='upstox_instruments')
    op.drop_index(op.f('ix_upstox_instruments_isin'), table_name='upstox_instruments')
    op.drop_index(op.f('ix_upstox_instruments_is_active'), table_name='upstox_instruments')
    op.drop_index(op.f('ix_upstox_instruments_instrument_key'), table_name='upstox_instruments')
    op.drop_index(op.f('ix_upstox_instruments_exchange'), table_name='upstox_instruments')
    op.drop_index('idx_upstox_instr_symbol_exchange', table_name='upstox_instruments')
    op.drop_table('upstox_instruments')

    # Drop upstox_tokens table
    op.drop_index(op.f('ix_upstox_tokens_is_active'), table_name='upstox_tokens')
    op.drop_index('idx_upstox_tokens_active_expires', table_name='upstox_tokens')
    op.drop_table('upstox_tokens')
