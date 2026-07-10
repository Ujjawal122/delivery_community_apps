"""add_post_type_and_bookmarks

Revision ID: 8ab9363b6b82
Revises: 946c16af0891
Create Date: 2026-07-06 13:10:59.215891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8ab9363b6b82'
down_revision: Union[str, Sequence[str], None] = '946c16af0891'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enum type and add column to posts
    posttype_enum = postgresql.ENUM('question', 'share', 'discussion', 'meme', 'tip', 'news', 'company_update', name='posttype')
    posttype_enum.create(op.get_bind())
    op.add_column('posts', sa.Column('post_type', posttype_enum, server_default='share', nullable=False))

    # 2. Create bookmarks table
    op.create_table('bookmarks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('post_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'post_id', name='uq_bookmark_user_post')
    )
    op.create_index(op.f('ix_bookmarks_id'), 'bookmarks', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_bookmarks_id'), table_name='bookmarks')
    op.drop_table('bookmarks')
    op.drop_column('posts', 'post_type')
    posttype_enum = postgresql.ENUM('question', 'share', 'discussion', 'meme', 'tip', 'news', 'company_update', name='posttype')
    posttype_enum.drop(op.get_bind())
