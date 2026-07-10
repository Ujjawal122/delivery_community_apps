"""add_is_revoked_to_refresh_tokens

Revision ID: 6fba4b103dd1
Revises: 
Create Date: 2026-07-04 23:29:58.733748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6fba4b103dd1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_revoked column to refresh_tokens table."""
    op.add_column(
        'refresh_tokens',
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )


def downgrade() -> None:
    """Remove is_revoked column from refresh_tokens table."""
    op.drop_column('refresh_tokens', 'is_revoked')
