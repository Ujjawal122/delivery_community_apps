"""add location and interests

Revision ID: 5eb1fce07ae8
Revises: 8ab9363b6b82
Create Date: 2026-07-07 16:21:24.101374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '5eb1fce07ae8'
down_revision: Union[str, Sequence[str], None] = '8ab9363b6b82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- Community additions ---
    # Create enum first
    community_purpose = postgresql.ENUM('education', 'fun', 'technology', 'sports', 'gaming', 'business', 'other', name='communitypurpose')
    community_purpose.create(op.get_bind())
    
    op.add_column('communities', sa.Column('unique_name', sa.String(length=255), nullable=True))
    op.add_column('communities', sa.Column('about', sa.Text(), nullable=True))
    op.add_column('communities', sa.Column('purpose', community_purpose, server_default='other', nullable=False))
    op.add_column('communities', sa.Column('is_public', sa.Boolean(), server_default='true', nullable=False))
    
    # We must populate unique_name before making it non-nullable (though we can just leave it nullable for old rows)
    op.execute("UPDATE communities SET unique_name = md5(random()::text) WHERE unique_name IS NULL")
    op.alter_column('communities', 'unique_name', nullable=False)
    op.create_index(op.f('ix_communities_unique_name'), 'communities', ['unique_name'], unique=True)
    
    op.drop_index('ix_communities_name', table_name='communities')
    op.drop_column('communities', 'description')

    # --- Comment additions ---
    op.add_column('comments', sa.Column('replied_to_user_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_comments_replied_user', 'comments', 'users', ['replied_to_user_id'], ['id'], ondelete='SET NULL')

    # --- User/Post additions (Location and Interests) ---
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
    op.add_column('users', sa.Column('interests', postgresql.ARRAY(sa.String()), nullable=True))
    
    op.add_column('users', sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True))

    op.add_column('posts', sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # --- User/Post ---
    op.drop_index('idx_posts_location', table_name='posts', postgresql_using='gist')
    op.drop_column('posts', 'location')
    op.drop_index('idx_users_location', table_name='users', postgresql_using='gist')
    op.drop_column('users', 'location')
    op.drop_column('users', 'interests')

    # --- Comments ---
    op.drop_constraint('fk_comments_replied_user', 'comments', type_='foreignkey')
    op.drop_column('comments', 'replied_to_user_id')

    # --- Communities ---
    op.add_column('communities', sa.Column('description', sa.Text(), nullable=True))
    op.drop_index(op.f('ix_communities_unique_name'), table_name='communities')
    op.create_index('ix_communities_name', 'communities', ['name'], unique=True)
    op.drop_column('communities', 'is_public')
    op.drop_column('communities', 'purpose')
    op.drop_column('communities', 'about')
    op.drop_column('communities', 'unique_name')
    
    op.execute("DROP TYPE communitypurpose")
