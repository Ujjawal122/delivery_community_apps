
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ApiResponse, created, no_data, ok
from app.dependencies import get_current_user, get_db, get_current_user_optional
from app.models.post import PostType
from app.models.user import User
from app.schemas.post import (
    CommentCreate,
    CommentUpdate,
    PostCreate,
    PostUpdate,
    VoteRequest,
    FeedRequest,
)
from app.services.post_service import CommentService, PostService
from app.services.feed_service import FeedService

router = APIRouter(tags=["Community"])




@router.post("/posts", response_model=ApiResponse, status_code=201,
             summary="Create a new community post")
async def create_post(
    data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    result = await PostService.create_post(db, current_user, data)
    await db.commit()
    return created(result, "Post created successfully")


@router.get("/posts", response_model=ApiResponse,
            summary="List all posts (paginated + filterable)")
async def list_posts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    post_type: Optional[PostType] = Query(None, description="Filter by post type"),
    community_id: Optional[uuid.UUID] = Query(None, description="Filter by community"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    result = await PostService.list_posts(db, page, limit, community_id, post_type, current_user.id)
    return ok(result, "Posts retrieved")


@router.post("/posts/feed", response_model=ApiResponse,
             summary="Get personalized post feed")
async def get_personalized_feed(
    data: FeedRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure radius_km is a float (provide default if None) to satisfy type requirement
    radius_km = data.radius_km if data.radius_km is not None else 5.0
    posts, total = await FeedService.get_personalized_feed(
        db,
        current_user.id,
        data.latitude,
        data.longitude,
        radius_km,
        data.page,
        data.limit,
    )
    from app.schemas.post import PaginatedPosts
    result_obj = PaginatedPosts.model_validate({
        "items": posts,
        "total": total,
        "page": data.page,
        "limit": data.limit
    })
    return ok(result_obj.model_dump(mode="json"), "Personalized feed retrieved")


@router.get("/posts/bookmarks", response_model=ApiResponse,
            summary="Get my bookmarked posts")
async def get_bookmarks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
  
    result = await PostService.get_bookmarks(db, current_user, page, limit)
    return ok(result, "Bookmarks retrieved")


@router.get("/posts/community/{community_id}", response_model=ApiResponse,
            summary="List posts for a specific community")
async def list_community_posts(
    community_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    post_type: Optional[PostType] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
   
    result = await PostService.list_posts(db, page, limit, community_id, post_type, current_user.id)
    return ok(result, "Community posts retrieved")


@router.get("/posts/{post_id}", response_model=ApiResponse,
            summary="Get post details")
async def get_post(
    post_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await PostService.get_post(db, post_id, current_user.id)
    return ok(result, "Post details retrieved")


@router.patch("/posts/{post_id}", response_model=ApiResponse,
              summary="Update your own post")
async def update_post(
    post_id: uuid.UUID,
    data: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    result = await PostService.update_post(db, current_user, post_id, data)
    await db.commit()
    return ok(result, "Post updated")


@router.delete("/posts/{post_id}", response_model=ApiResponse,
               summary="Delete your own post")
async def delete_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    await PostService.delete_post(db, current_user, post_id)
    await db.commit()
    return no_data("Post deleted successfully")


@router.post("/posts/{post_id}/vote", response_model=ApiResponse,
             summary="Vote on a post (up or down)")
async def vote_post(
    post_id: uuid.UUID,
    data: VoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    result = await PostService.vote_post(db, current_user, post_id, data.vote_type)
    await db.commit()
    return ok(result, "Vote recorded")


@router.delete("/posts/{post_id}/vote", response_model=ApiResponse,
               summary="Remove your vote from a post")
async def remove_post_vote(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
   
    result = await PostService.remove_vote(db, current_user, post_id)
    await db.commit()
    return ok(result, "Vote removed")


@router.post("/posts/{post_id}/bookmark", response_model=ApiResponse,
             summary="Toggle bookmark on a post")
async def toggle_bookmark(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
   
    result = await PostService.toggle_bookmark(db, current_user, post_id)
    await db.commit()
    return ok(result, result.message)



@router.post("/posts/{post_id}/comments", response_model=ApiResponse, status_code=201,
             summary="Add a comment or reply to a post")
async def create_comment(
    post_id: uuid.UUID,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
   
    result = await CommentService.create_comment(db, current_user, post_id, data)
    await db.commit()
    return created(result, "Comment added")


@router.get("/posts/{post_id}/comments", response_model=ApiResponse,
            summary="List comments for a post (with nested replies)")
async def list_comments(
    post_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
   
    result = await CommentService.list_comments(db, current_user, post_id, page, limit)
    return ok(result, "Comments retrieved")


@router.patch("/posts/{post_id}/comments/{comment_id}", response_model=ApiResponse,
              summary="Update your own comment")
async def update_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    data: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
   
    result = await CommentService.update_comment(db, current_user, comment_id, data)
    await db.commit()
    return ok(result, "Comment updated")


@router.delete("/posts/{post_id}/comments/{comment_id}", response_model=ApiResponse,
               summary="Delete your own comment")
async def delete_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    await CommentService.delete_comment(db, current_user, comment_id)
    await db.commit()
    return no_data("Comment deleted")


@router.post("/posts/{post_id}/comments/{comment_id}/vote", response_model=ApiResponse,
             summary="Vote on a comment")
async def vote_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    data: VoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔐 Bearer token required. Same toggle logic as post votes."""
    result = await CommentService.vote_comment(db, current_user, comment_id, data.vote_type)
    await db.commit()
    return ok(result, "Vote recorded")


@router.delete("/posts/{post_id}/comments/{comment_id}/vote", response_model=ApiResponse,
               summary="Remove your vote from a comment")
async def remove_comment_vote(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔐 Bearer token required."""
    result = await CommentService.remove_comment_vote(db, current_user, comment_id)
    await db.commit()
    return ok(result, "Vote removed")
