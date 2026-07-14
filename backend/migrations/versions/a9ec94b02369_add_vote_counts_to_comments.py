"""Add vote counts to comments

Revision ID: a9ec94b02369
Revises: 34242d6dbde1
Create Date: 2026-07-11 16:20:13.389497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a9ec94b02369'
down_revision: Union[str, Sequence[str], None] = '34242d6dbde1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('comments', sa.Column('upvotes_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('comments', sa.Column('downvotes_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('comments', 'downvotes_count')
    op.drop_column('comments', 'upvotes_count')
