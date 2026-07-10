"""add_post_type_and_bookmarks

Revision ID: 946c16af0891
Revises: 6fba4b103dd1
Create Date: 2026-07-06 12:38:50.998624
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "946c16af0891"
down_revision: Union[str, Sequence[str], None] = "6fba4b103dd1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# PostgreSQL enum name must match the SQLAlchemy Enum definition
_post_type_enum = sa.Enum(
    "question", "share", "discussion", "meme", "tip", "news", "company_update",
    name="posttype",
)


def upgrade() -> None:
    # 1. Create the posttype enum then add the column to posts
    _post_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "posts",
        sa.Column(
            "post_type",
            sa.Enum(
                "question", "share", "discussion", "meme", "tip", "news", "company_update",
                name="posttype",
            ),
            nullable=False,
            server_default="share",
        ),
    )
    op.create_index("ix_posts_post_type", "posts", ["post_type"])

    # 2. Create bookmarks table
    op.create_table(
        "bookmarks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "post_id", name="uq_bookmark_user_post"),
    )
    op.create_index("ix_bookmarks_user_id", "bookmarks", ["user_id"])
    op.create_index("ix_bookmarks_post_id", "bookmarks", ["post_id"])


def downgrade() -> None:
    op.drop_table("bookmarks")
    op.drop_index("ix_posts_post_type", table_name="posts")
    op.drop_column("posts", "post_type")
    _post_type_enum.drop(op.get_bind(), checkfirst=True)
