"""Add push_token to users

Revision ID: e542f43d03ea
Revises: dd199c41822d
Create Date: 2026-07-10 12:36:18.165635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e542f43d03ea'
down_revision: Union[str, Sequence[str], None] = 'dd199c41822d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('push_token', sa.String(length=255), nullable=True))
    op.alter_column('users', 'is_verified',
               existing_type=sa.BOOLEAN(),
               nullable=False)


def downgrade() -> None:
    op.alter_column('users', 'is_verified',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.drop_column('users', 'push_token')
