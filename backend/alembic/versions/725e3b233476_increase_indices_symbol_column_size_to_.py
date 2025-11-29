"""Increase indices.symbol column size to VARCHAR(100) for long index names

Revision ID: 725e3b233476
Revises: 33796dd55aff
Create Date: 2025-11-29 10:11:05.133090

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '725e3b233476'
down_revision = '33796dd55aff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Increase symbol column size from VARCHAR(50) to VARCHAR(100)
    # This is needed for long NSE index names like:
    # "NIFTY500 MULTICAP INDIA MANUFACTURING 50:30:20"
    # "NIFTY INDIA CORPORATE GROUP INDEX - TATA GROUP"
    op.alter_column('indices', 'symbol',
                    existing_type=sa.VARCHAR(length=50),
                    type_=sa.VARCHAR(length=100),
                    existing_nullable=False)


def downgrade() -> None:
    # Revert back to VARCHAR(50)
    # WARNING: This may fail if there are values longer than 50 characters
    op.alter_column('indices', 'symbol',
                    existing_type=sa.VARCHAR(length=100),
                    type_=sa.VARCHAR(length=50),
                    existing_nullable=False)
