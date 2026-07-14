"""Add follow system

Revision ID: ed7210ed4b51
Revises: a9ec94b02369
Create Date: 2026-07-13 12:47:26.887673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ed7210ed4b51'
down_revision: Union[str, Sequence[str], None] = 'a9ec94b02369'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('follows',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('follower_id', sa.UUID(), nullable=False),
    sa.Column('following_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('follower_id != following_id', name='ck_no_self_follow'),
    sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['following_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('follower_id', 'following_id', name='uq_follower_following')
    )
    op.create_index(op.f('ix_follows_follower_id'), 'follows', ['follower_id'], unique=False)
    op.create_index(op.f('ix_follows_following_id'), 'follows', ['following_id'], unique=False)
    
    op.add_column('users', sa.Column('username', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('follower_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('following_count', sa.Integer(), server_default='0', nullable=False))
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'following_count')
    op.drop_column('users', 'follower_count')
    op.drop_column('users', 'username')
    
    op.drop_index(op.f('ix_follows_following_id'), table_name='follows')
    op.drop_index(op.f('ix_follows_follower_id'), table_name='follows')
    op.drop_table('follows')
