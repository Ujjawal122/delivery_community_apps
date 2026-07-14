"""
app/repositories/post_repository.py
DB access layer for Posts, Comments, Votes, and Bookmarks.
"""

import uuid
from typing import Optional, Sequence

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.post import Bookmark, Comment, CommentVote, Post, PostType, PostVote
from app.repositories.base import BaseRepository


# ── Post Repository ────────────────────────────────────────────────

class PostRepository(BaseRepository[Post]):
    model = Post

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        title: str,
        post_type: PostType,
        content: Optional[str] = None,
        image: Optional[str] = None,
        video: Optional[str] = None,
        community_id: Optional[uuid.UUID] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Post:
        from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
        post = Post(
            user_id=user_id,
            title=title,
            post_type=post_type,
            content=content,
            image=image,
            video=video,
            community_id=community_id,
        )
        if latitude is not None and longitude is not None:
            post.location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            post.latitude = latitude
            post.longitude = longitude
            
        self.add(post)
        await self.flush()
        await self.refresh(post)
        return post

    async def get_by_id_with_author(self, post_id: uuid.UUID) -> Optional[Post]:
        """Load post with author eagerly (avoids lazy-load errors)."""
        result = await self.db.execute(
            select(Post)
            .where(Post.id == post_id)
            .options(selectinload(Post.author))
        )
        return result.scalar_one_or_none()

    async def list_posts(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        community_id: Optional[uuid.UUID] = None,
        post_type: Optional[PostType] = None,
    ) -> tuple[Sequence[Post], int]:
        """Returns (posts, total_count) with author eager-loaded."""
        q = select(Post).options(selectinload(Post.author))
        count_q = select(func.count()).select_from(Post)

        if community_id is not None:
            q = q.where(Post.community_id == community_id)
            count_q = count_q.where(Post.community_id == community_id)
        if post_type is not None:
            q = q.where(Post.post_type == post_type)
            count_q = count_q.where(Post.post_type == post_type)

        q = q.order_by(Post.created_at.desc()).offset(offset).limit(limit)

        rows = await self.db.execute(q)
        total_row = await self.db.execute(count_q)
        return rows.scalars().all(), total_row.scalar_one()

    async def get_vote(self, user_id: uuid.UUID, post_id: uuid.UUID) -> Optional[PostVote]:
        result = await self.db.execute(
            select(PostVote).where(
                PostVote.user_id == user_id,
                PostVote.post_id == post_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_vote(
        self, user_id: uuid.UUID, post_id: uuid.UUID, vote_value: int
    ) -> Optional[int]:
        """
        Insert or update vote. Returns old vote_type (or None if new).
        Caller is responsible for adjusting upvotes_count / downvotes_count.
        """
        existing = await self.get_vote(user_id, post_id)
        old_type = existing.vote_type if existing else None

        if existing:
            existing.vote_type = vote_value
        else:
            vote = PostVote(user_id=user_id, post_id=post_id, vote_type=vote_value)
            self.db.add(vote)

        await self.db.flush()
        return old_type

    async def remove_vote(self, user_id: uuid.UUID, post_id: uuid.UUID) -> Optional[int]:
        """Delete vote if exists, return its vote_type or None."""
        existing = await self.get_vote(user_id, post_id)
        if not existing:
            return None
        old_type = existing.vote_type
        await self.db.delete(existing)
        await self.db.flush()
        return old_type


# ── Comment Repository ─────────────────────────────────────────────

class CommentRepository(BaseRepository[Comment]):
    model = Comment

    async def create(
        self,
        *,
        post_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        parent_id: Optional[uuid.UUID] = None,
        replied_to_user_id: Optional[uuid.UUID] = None,
    ) -> Comment:
        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id,
            replied_to_user_id=replied_to_user_id,
        )
        self.add(comment)
        await self.flush()
        await self.refresh(comment)
        return comment

    async def get_by_id_with_author(self, comment_id: uuid.UUID) -> Optional[Comment]:
        result = await self.db.execute(
            select(Comment)
            .where(Comment.id == comment_id)
            .options(
                selectinload(Comment.author),
                selectinload(Comment.replied_to_user),
                selectinload(Comment.replies)
                    .selectinload(Comment.author),
                selectinload(Comment.replies)
                    .selectinload(Comment.replied_to_user),
                selectinload(Comment.replies)
                    .selectinload(Comment.replies)
                    .selectinload(Comment.author),
            )
        )
        return result.scalar_one_or_none()

    async def list_top_level(
        self,
        post_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Comment]:
        """Returns top-level comments (no parent) with author + 2-level replies eager-loaded."""
        result = await self.db.execute(
            select(Comment)
            .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
            .options(
                selectinload(Comment.author),
                selectinload(Comment.replied_to_user),
                selectinload(Comment.replies)
                    .selectinload(Comment.author),
                selectinload(Comment.replies)
                    .selectinload(Comment.replied_to_user),
                selectinload(Comment.replies)
                    .selectinload(Comment.replies)
                    .selectinload(Comment.author),
            )
            .order_by(Comment.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_vote(self, user_id: uuid.UUID, comment_id: uuid.UUID) -> Optional[CommentVote]:
        result = await self.db.execute(
            select(CommentVote).where(
                CommentVote.user_id == user_id,
                CommentVote.comment_id == comment_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_vote(
        self, user_id: uuid.UUID, comment_id: uuid.UUID, vote_value: int
    ) -> Optional[int]:
        existing = await self.get_vote(user_id, comment_id)
        old_type = existing.vote_type if existing else None
        if existing:
            existing.vote_type = vote_value
        else:
            vote = CommentVote(user_id=user_id, comment_id=comment_id, vote_type=vote_value)
            self.db.add(vote)
        await self.db.flush()
        return old_type

    async def remove_vote(self, user_id: uuid.UUID, comment_id: uuid.UUID) -> Optional[int]:
        existing = await self.get_vote(user_id, comment_id)
        if not existing:
            return None
        old_type = existing.vote_type
        await self.db.delete(existing)
        await self.db.flush()
        return old_type


# ── Bookmark Repository ────────────────────────────────────────────

class BookmarkRepository(BaseRepository[Bookmark]):
    model = Bookmark

    async def get(self, user_id: uuid.UUID, post_id: uuid.UUID) -> Optional[Bookmark]:
        result = await self.db.execute(
            select(Bookmark).where(
                Bookmark.user_id == user_id,
                Bookmark.post_id == post_id,
            )
        )
        return result.scalar_one_or_none()

    async def toggle(self, user_id: uuid.UUID, post_id: uuid.UUID) -> bool:
        """Returns True if bookmarked (added), False if removed."""
        existing = await self.get(user_id, post_id)
        if existing:
            await self.db.delete(existing)
            await self.db.flush()
            return False
        else:
            bm = Bookmark(user_id=user_id, post_id=post_id)
            self.db.add(bm)
            await self.db.flush()
            return True

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Post], int]:
        """Returns bookmarked Posts (with author) and total count."""
        # Join Bookmark → Post, eager-load Post.author
        q = (
            select(Post)
            .join(Bookmark, Bookmark.post_id == Post.id)
            .where(Bookmark.user_id == user_id)
            .options(selectinload(Post.author))
            .order_by(Bookmark.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_q = (
            select(func.count())
            .select_from(Bookmark)
            .where(Bookmark.user_id == user_id)
        )
        rows = await self.db.execute(q)
        total = await self.db.execute(count_q)
        return rows.scalars().all(), total.scalar_one()
