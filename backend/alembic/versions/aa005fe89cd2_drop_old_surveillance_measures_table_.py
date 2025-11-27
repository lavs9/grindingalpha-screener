"""Drop old surveillance_measures table and ensure 4-table normalized design

Revision ID: aa005fe89cd2
Revises: f77b45d8af68
Create Date: 2025-11-27 09:25:01.239885

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa005fe89cd2'
down_revision = 'f77b45d8af68'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Drop old surveillance_measures table and replace with 4-table normalized design.
    The new tables (surveillance_list, surveillance_fundamental_flags,
    surveillance_price_movement, surveillance_price_variation) were already created
    in the database, so this migration just cleans up the old table.
    """
    # Drop the old surveillance_measures table (replaced by 4-table design)
    op.drop_table('surveillance_measures')


def downgrade() -> None:
    """
    Recreate old surveillance_measures table.
    Note: Data migration is not included - this is just schema rollback.
    """
    op.create_table(
        'surveillance_measures',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('security_name', sa.String(length=255)),
        sa.Column('measure_type', sa.String(length=100)),
        sa.Column('reason', sa.String(length=500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_surveillance_date_symbol', 'surveillance_measures', ['date', 'symbol'])
    op.create_index('idx_surveillance_measure_type', 'surveillance_measures', ['measure_type'])
    op.create_index(op.f('ix_surveillance_measures_date'), 'surveillance_measures', ['date'])
