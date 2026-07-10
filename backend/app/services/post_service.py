"""
app/services/post_service.py
Business logic for Posts, Comments, Votes, and Bookmarks.

Vote behaviour:
  - Same vote again  → removes it (toggle off)
  - Opposite vote    → switches it (adjusts both counters)
  - New vote         → adds it
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.post import PostType
from app.models.user import User
from app.repositories.post_repository import (
    BookmarkRepository,
    CommentRepository,
    PostRepository,
)
from app.schemas.post import (
    BookmarkToggleResponse,
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    PaginatedPosts,
    PostCreate,
    PostResponse,
    PostUpdate,
)

logger = get_logger(__name__)


# ── Helpers ────────────────────────────────────────────────────────

def _post_response(post) -> PostResponse:
    return PostResponse.model_validate(post)


def _comment_response(comment) -> CommentResponse:
    return CommentResponse.model_validate(comment)


def _page_offset(page: int, limit: int) -> int:
    return (page - 1) * limit


# ── Post Service ───────────────────────────────────────────────────

class PostService:

    # ── Create ─────────────────────────────────────────────────

    @staticmethod
    async def create_post(
        db: AsyncSession,
        current_user: User,
        data: PostCreate,
    ) -> PostResponse:
        repo = PostRepository(db)
        post = await repo.create(
            user_id=current_user.id,
            title=data.title,
            post_type=data.post_type,
            content=data.content,
            image=data.image,
            video=data.video,
            community_id=data.community_id,
            latitude=data.latitude,
            longitude=data.longitude,
        )
        # reload with author
        post = await repo.get_by_id_with_author(post.id)
        logger.info("post_created", extra={"post_id": str(post.id), "user_id": str(current_user.id)})
        return _post_response(post)

    # ── Get single post ────────────────────────────────────────

    @staticmethod
    async def get_post(db: AsyncSession, post_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> PostResponse:
        repo = PostRepository(db)
        post = await repo.get_by_id_with_author(post_id)
        if not post:
            raise NotFoundError("Post not found")
            
        if user_id:
            from app.models.post import PostVote
            from sqlalchemy import select
            vote_stmt = select(PostVote.vote_type).where(
                PostVote.user_id == user_id, 
                PostVote.post_id == post_id
            )
            vote_res = await db.execute(vote_stmt)
            post.user_vote = vote_res.scalar_one_or_none()
            
        return _post_response(post)

    # ── List posts ─────────────────────────────────────────────

    @staticmethod
    async def list_posts(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        community_id: Optional[uuid.UUID] = None,
        post_type: Optional[PostType] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> PaginatedPosts:
        repo = PostRepository(db)
        offset = _page_offset(page, limit)
        posts, total = await repo.list_posts(
            offset=offset,
            limit=limit,
            community_id=community_id,
            post_type=post_type,
        )
        
        if posts and user_id:
            from app.models.post import PostVote
            from sqlalchemy import select
            post_ids = [p.id for p in posts]
            votes_stmt = select(PostVote).where(
                PostVote.user_id == user_id,
                PostVote.post_id.in_(post_ids)
            )
            votes_res = await db.execute(votes_stmt)
            vote_map = {v.post_id: v.vote_type for v in votes_res.scalars().all()}
            for p in posts:
                p.user_vote = vote_map.get(p.id)

        return PaginatedPosts(
            items=[_post_response(p) for p in posts],
            total=total,
            page=page,
            limit=limit,
        )

    # ── Update post ────────────────────────────────────────────

    @staticmethod
    async def update_post(
        db: AsyncSession,
        current_user: User,
        post_id: uuid.UUID,
        data: PostUpdate,
    ) -> PostResponse:
        repo = PostRepository(db)
        post = await repo.get_by_id_with_author(post_id)
        if not post:
            raise NotFoundError("Post not found")
        if post.user_id != current_user.id:
            raise ForbiddenError("You can only edit your own posts")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(post, field, value)

        await db.flush()
        await db.refresh(post)
        logger.info("post_updated", extra={"post_id": str(post_id)})
        return _post_response(post)

    # ── Delete post ────────────────────────────────────────────

    @staticmethod
    async def delete_post(
        db: AsyncSession,
        current_user: User,
        post_id: uuid.UUID,
    ) -> None:
        repo = PostRepository(db)
        post = await repo.get_by_id(post_id)
        if not post:
            raise NotFoundError("Post not found")
        if post.user_id != current_user.id:
            raise ForbiddenError("You can only delete your own posts")
        await repo.delete(post)
        await db.flush()
        logger.info("post_deleted", extra={"post_id": str(post_id)})

    # ── Vote on post ───────────────────────────────────────────

    @staticmethod
    async def vote_post(
        db: AsyncSession,
        current_user: User,
        post_id: uuid.UUID,
        vote_type: str,          # "up" or "down"
    ) -> PostResponse:
        repo = PostRepository(db)
        post = await repo.get_by_id_with_author(post_id)
        if not post:
            raise NotFoundError("Post not found")

        vote_value = 1 if vote_type == "up" else -1
        old_type = await repo.upsert_vote(current_user.id, post_id, vote_value)

        if old_type is None:
            # New vote
            if vote_value == 1:
                post.upvotes_count += 1
            else:
                post.downvotes_count += 1
        elif old_type == vote_value:
            # Same vote → toggle off (remove)
            await repo.remove_vote(current_user.id, post_id)
            if vote_value == 1:
                post.upvotes_count = max(0, post.upvotes_count - 1)
            else:
                post.downvotes_count = max(0, post.downvotes_count - 1)
        else:
            # Opposite vote → switch
            if vote_value == 1:
                post.upvotes_count += 1
                post.downvotes_count = max(0, post.downvotes_count - 1)
            else:
                post.downvotes_count += 1
                post.upvotes_count = max(0, post.upvotes_count - 1)

        await db.flush()
        await db.refresh(post)
        return _post_response(post)

    # ── Remove vote from post ──────────────────────────────────

    @staticmethod
    async def remove_vote(
        db: AsyncSession,
        current_user: User,
        post_id: uuid.UUID,
    ) -> PostResponse:
        repo = PostRepository(db)
        post = await repo.get_by_id_with_author(post_id)
        if not post:
            raise NotFoundError("Post not found")

        old_type = await repo.remove_vote(current_user.id, post_id)
        if old_type is None:
            raise BadRequestError("You have not voted on this post")

        if old_type == 1:
            post.upvotes_count = max(0, post.upvotes_count - 1)
        else:
            post.downvotes_count = max(0, post.downvotes_count - 1)

        await db.flush()
        await db.refresh(post)
        return _post_response(post)

    # ── Toggle bookmark ────────────────────────────────────────

    @staticmethod
    async def toggle_bookmark(
        db: AsyncSession,
        current_user: User,
        post_id: uuid.UUID,
    ) -> BookmarkToggleResponse:
        repo = PostRepository(db)
        post = await repo.get_by_id(post_id)
        if not post:
            raise NotFoundError("Post not found")

        bm_repo = BookmarkRepository(db)
        bookmarked = await bm_repo.toggle(current_user.id, post_id)
        msg = "Post bookmarked" if bookmarked else "Bookmark removed"
        logger.info("bookmark_toggled", extra={
            "user_id": str(current_user.id),
            "post_id": str(post_id),
            "bookmarked": bookmarked,
        })
        return BookmarkToggleResponse(bookmarked=bookmarked, message=msg)

    # ── Get bookmarks ──────────────────────────────────────────

    @staticmethod
    async def get_bookmarks(
        db: AsyncSession,
        current_user: User,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedPosts:
        bm_repo = BookmarkRepository(db)
        offset = _page_offset(page, limit)
        posts, total = await bm_repo.list_by_user(current_user.id, offset, limit)
        return PaginatedPosts(
            items=[_post_response(p) for p in posts],
            total=total,
            page=page,
            limit=limit,
        )


# ── Comment Service ────────────────────────────────────────────────

class CommentService:

    # ── Create comment / reply ─────────────────────────────────

    @staticmethod
    async def create_comment(
        db: AsyncSession,
        current_user: User,
        post_id: uuid.UUID,
        data: CommentCreate,
    ) -> CommentResponse:
        post_repo = PostRepository(db)
        if not await post_repo.get_by_id(post_id):
            raise NotFoundError("Post not found")

        comment_repo = CommentRepository(db)

        # Validate parent comment belongs to same post
        if data.parent_id:
            parent = await comment_repo.get_by_id(data.parent_id)
            if not parent or parent.post_id != post_id:
                raise BadRequestError("Parent comment not found on this post")

        comment = await comment_repo.create(
            post_id=post_id,
            user_id=current_user.id,
            content=data.content,
            parent_id=data.parent_id,
            replied_to_user_id=data.replied_to_user_id,
        )
        comment = await comment_repo.get_by_id_with_author(comment.id)
        logger.info("comment_created", extra={
            "comment_id": str(comment.id),
            "post_id": str(post_id),
        })
        return _comment_response(comment)

    # ── List comments for a post ───────────────────────────────

    @staticmethod
    async def list_comments(
        db: AsyncSession,
        post_id: uuid.UUID,
        page: int = 1,
        limit: int = 50,
    ) -> list[CommentResponse]:
        post_repo = PostRepository(db)
        if not await post_repo.get_by_id(post_id):
            raise NotFoundError("Post not found")

        comment_repo = CommentRepository(db)
        offset = _page_offset(page, limit)
        comments = await comment_repo.list_top_level(post_id, offset, limit)
        return [_comment_response(c) for c in comments]

    # ── Update comment ─────────────────────────────────────────

    @staticmethod
    async def update_comment(
        db: AsyncSession,
        current_user: User,
        comment_id: uuid.UUID,
        data: CommentUpdate,
    ) -> CommentResponse:
        comment_repo = CommentRepository(db)
        comment = await comment_repo.get_by_id_with_author(comment_id)
        if not comment:
            raise NotFoundError("Comment not found")
        if comment.user_id != current_user.id:
            raise ForbiddenError("You can only edit your own comments")

        comment.content = data.content
        await db.flush()
        await db.refresh(comment)
        return _comment_response(comment)

    # ── Delete comment ─────────────────────────────────────────

    @staticmethod
    async def delete_comment(
        db: AsyncSession,
        current_user: User,
        comment_id: uuid.UUID,
    ) -> None:
        comment_repo = CommentRepository(db)
        comment = await comment_repo.get_by_id(comment_id)
        if not comment:
            raise NotFoundError("Comment not found")
        if comment.user_id != current_user.id:
            raise ForbiddenError("You can only delete your own comments")
        await comment_repo.delete(comment)
        await db.flush()
        logger.info("comment_deleted", extra={"comment_id": str(comment_id)})

    # ── Vote on comment ────────────────────────────────────────

    @staticmethod
    async def vote_comment(
        db: AsyncSession,
        current_user: User,
        comment_id: uuid.UUID,
        vote_type: str,
    ) -> CommentResponse:
        comment_repo = CommentRepository(db)
        comment = await comment_repo.get_by_id_with_author(comment_id)
        if not comment:
            raise NotFoundError("Comment not found")

        vote_value = 1 if vote_type == "up" else -1
        old_type = await comment_repo.upsert_vote(current_user.id, comment_id, vote_value)

        # Same toggle logic as post votes
        if old_type == vote_value:
            await comment_repo.remove_vote(current_user.id, comment_id)

        await db.flush()
        await db.refresh(comment)
        return _comment_response(comment)

    # ── Remove comment vote ────────────────────────────────────

    @staticmethod
    async def remove_comment_vote(
        db: AsyncSession,
        current_user: User,
        comment_id: uuid.UUID,
    ) -> CommentResponse:
        comment_repo = CommentRepository(db)
        comment = await comment_repo.get_by_id_with_author(comment_id)
        if not comment:
            raise NotFoundError("Comment not found")

        old_type = await comment_repo.remove_vote(current_user.id, comment_id)
        if old_type is None:
            raise BadRequestError("You have not voted on this comment")

        await db.flush()
        await db.refresh(comment)
        return _comment_response(comment)
