"""add latitude and longitude columns

Revision ID: 0643e81d8327
Revises: ed7210ed4b51
Create Date: 2026-07-13 16:04:46.344359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0643e81d8327'
down_revision: Union[str, Sequence[str], None] = 'ed7210ed4b51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns
    for table in ['users', 'posts', 'hazard_reports', 'gates']:
        op.add_column(table, sa.Column('latitude', sa.Float(), nullable=True))
        op.add_column(table, sa.Column('longitude', sa.Float(), nullable=True))
        
        # Backfill data from PostGIS location
        # The cast to geometry is needed for Geography columns (like in hazard_reports and gates)
        op.execute(f"UPDATE {table} SET latitude = ST_Y(location::geometry), longitude = ST_X(location::geometry) WHERE location IS NOT NULL")


def downgrade() -> None:
    """Downgrade schema."""
    for table in ['users', 'posts', 'hazard_reports', 'gates']:
        op.drop_column(table, 'longitude')
        op.drop_column(table, 'latitude')
