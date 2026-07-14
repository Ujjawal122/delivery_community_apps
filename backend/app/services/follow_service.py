import uuid
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete, func, text, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.user import User
from app.models.follow import Follow
from app.models.auth import Notification
from app.services.push_service import send_push_notification

logger = logging.getLogger(__name__)

class FollowService:

    @staticmethod
    async def is_mutual_follower(db: AsyncSession, user_id_1: uuid.UUID, user_id_2: uuid.UUID) -> bool:
        """Check if user 1 and user 2 mutually follow each other."""
        stmt = select(func.count(Follow.id)).where(
            or_(
                and_(Follow.follower_id == user_id_1, Follow.following_id == user_id_2),
                and_(Follow.follower_id == user_id_2, Follow.following_id == user_id_1)
            )
        )
        result = await db.execute(stmt)
        count = result.scalar_one()
        return count == 2

    @staticmethod
    async def _get_follow_statuses(db: AsyncSession, current_user_id: uuid.UUID, target_user_ids: List[uuid.UUID]) -> Dict[uuid.UUID, Dict[str, bool]]:
        """Batch fetch follow status (is_following, is_followed_by) for a list of users relative to current user."""
        if not target_user_ids:
            return {}

        # Get all records where current_user is follower or following among target users
        stmt = select(Follow.follower_id, Follow.following_id).where(
            or_(
                and_(Follow.follower_id == current_user_id, Follow.following_id.in_(target_user_ids)),
                and_(Follow.following_id == current_user_id, Follow.follower_id.in_(target_user_ids))
            )
        )
        result = await db.execute(stmt)
        records = result.all()

        statuses = {uid: {"is_following": False, "is_followed_by": False} for uid in target_user_ids}
        
        for follower_id, following_id in records:
            if follower_id == current_user_id:
                statuses[following_id]["is_following"] = True
            elif following_id == current_user_id:
                statuses[follower_id]["is_followed_by"] = True

        for uid in target_user_ids:
            statuses[uid]["is_mutual"] = statuses[uid]["is_following"] and statuses[uid]["is_followed_by"]

        return statuses

    @staticmethod
    async def search_users(db: AsyncSession, query: str, limit: int, offset: int, current_user_id: uuid.UUID) -> tuple[List[dict], int]:
        """Search users by email or username."""
        # Clean query
        q = f"%{query}%"

        # Count total
        count_stmt = select(func.count(User.id)).where(
            and_(
                User.id != current_user_id,
                or_(User.email.ilike(q), User.username.ilike(q), User.full_name.ilike(q))
            )
        )
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        # Fetch users
        stmt = select(User).where(
            and_(
                User.id != current_user_id,
                or_(User.email.ilike(q), User.username.ilike(q), User.full_name.ilike(q))
            )
        ).order_by(User.full_name.asc()).limit(limit).offset(offset)
        
        result = await db.execute(stmt)
        users = result.scalars().all()

        # Map to dict and inject follow status
        user_ids = [u.id for u in users]
        statuses = await FollowService._get_follow_statuses(db, current_user_id, user_ids)

        items = []
        for u in users:
            u_dict = {
                "id": u.id,
                "full_name": u.full_name,
                "username": u.username,
                "email": u.email,
                "avatar": u.avatar,
                "follower_count": u.follower_count,
                "following_count": u.following_count,
                "is_following": statuses.get(u.id, {}).get("is_following", False),
                "is_followed_by": statuses.get(u.id, {}).get("is_followed_by", False),
                "is_mutual": statuses.get(u.id, {}).get("is_mutual", False)
            }
            items.append(u_dict)

        return items, total

    @staticmethod
    async def get_followers(db: AsyncSession, user_id: uuid.UUID, limit: int, offset: int, current_user_id: uuid.UUID) -> tuple[List[dict], int]:
        """Get followers of a user."""
        count_stmt = select(func.count(Follow.id)).where(Follow.following_id == user_id)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = (
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
            .order_by(Follow.created_at.desc())
            .limit(limit).offset(offset)
        )
        res = await db.execute(stmt)
        users = res.scalars().all()

        user_ids = [u.id for u in users]
        statuses = await FollowService._get_follow_statuses(db, current_user_id, user_ids)

        items = []
        for u in users:
            items.append({
                "id": u.id,
                "full_name": u.full_name,
                "username": u.username,
                "email": u.email,
                "avatar": u.avatar,
                "follower_count": u.follower_count,
                "following_count": u.following_count,
                "is_following": statuses.get(u.id, {}).get("is_following", False),
                "is_followed_by": statuses.get(u.id, {}).get("is_followed_by", False),
                "is_mutual": statuses.get(u.id, {}).get("is_mutual", False)
            })

        return items, total

    @staticmethod
    async def get_following(db: AsyncSession, user_id: uuid.UUID, limit: int, offset: int, current_user_id: uuid.UUID) -> tuple[List[dict], int]:
        """Get users followed by a user."""
        count_stmt = select(func.count(Follow.id)).where(Follow.follower_id == user_id)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = (
            select(User)
            .join(Follow, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
            .order_by(Follow.created_at.desc())
            .limit(limit).offset(offset)
        )
        res = await db.execute(stmt)
        users = res.scalars().all()

        user_ids = [u.id for u in users]
        statuses = await FollowService._get_follow_statuses(db, current_user_id, user_ids)

        items = []
        for u in users:
            items.append({
                "id": u.id,
                "full_name": u.full_name,
                "username": u.username,
                "email": u.email,
                "avatar": u.avatar,
                "follower_count": u.follower_count,
                "following_count": u.following_count,
                "is_following": statuses.get(u.id, {}).get("is_following", False),
                "is_followed_by": statuses.get(u.id, {}).get("is_followed_by", False),
                "is_mutual": statuses.get(u.id, {}).get("is_mutual", False)
            })

        return items, total

    @staticmethod
    async def get_suggestions(db: AsyncSession, current_user_id: uuid.UUID, limit: int = 20) -> List[dict]:
        """Get user suggestions (users not currently followed, excluding self)."""
        # Exclude self and already followed
        subq = select(Follow.following_id).where(Follow.follower_id == current_user_id)
        
        stmt = (
            select(User)
            .where(and_(User.id != current_user_id, ~User.id.in_(subq)))
            .order_by(User.created_at.desc()) # Or random via func.random()
            .limit(limit)
        )
        res = await db.execute(stmt)
        users = res.scalars().all()

        # Follow statuses (they shouldn't be following, but could be followed by them)
        user_ids = [u.id for u in users]
        statuses = await FollowService._get_follow_statuses(db, current_user_id, user_ids)

        items = []
        for u in users:
            items.append({
                "id": u.id,
                "full_name": u.full_name,
                "username": u.username,
                "email": u.email,
                "avatar": u.avatar,
                "follower_count": u.follower_count,
                "following_count": u.following_count,
                "is_following": False, # by definition
                "is_followed_by": statuses.get(u.id, {}).get("is_followed_by", False),
                "is_mutual": False
            })

        return items

    @staticmethod
    async def follow_user(db: AsyncSession, follower_user: User, following_id: uuid.UUID) -> dict:
        """Follow another user."""
        if follower_user.id == following_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")

        # Check if target user exists
        stmt = select(User).where(User.id == following_id)
        res = await db.execute(stmt)
        target_user = res.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if already following
        stmt = select(Follow).where(and_(Follow.follower_id == follower_user.id, Follow.following_id == following_id))
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already following this user")

        # Create Follow
        new_follow = Follow(follower_id=follower_user.id, following_id=following_id)
        db.add(new_follow)

        # Update Counts
        target_user.follower_count += 1
        follower_user.following_count += 1

        # Check Mutual Follow
        is_mutual = await FollowService.is_mutual_follower(db, follower_user.id, following_id)
        # Note: at this point, `new_follow` is not committed but it's in the session.
        # Wait, is_mutual_follower executes a new query that might not see `new_follow` if not flushed.
        await db.flush()
        is_mutual = await FollowService.is_mutual_follower(db, follower_user.id, following_id)

        # Notifications
        notif1 = Notification(
            user_id=following_id,
            title="New Follower",
            body=f"{follower_user.full_name} started following you."
        )
        db.add(notif1)

        # If push token exists, notify
        if target_user.push_token:
            await send_push_notification(target_user.push_token, notif1.title, notif1.body)

        if is_mutual:
            notif2 = Notification(
                user_id=following_id,
                title="Mutual Follow",
                body=f"You and {follower_user.full_name} can now chat!"
            )
            notif3 = Notification(
                user_id=follower_user.id,
                title="Mutual Follow",
                body=f"You and {target_user.full_name} can now chat!"
            )
            db.add_all([notif2, notif3])
            
            if target_user.push_token:
                await send_push_notification(target_user.push_token, notif2.title, notif2.body)
            if follower_user.push_token:
                await send_push_notification(follower_user.push_token, notif3.title, notif3.body)

        await db.commit()
        await db.refresh(follower_user)
        
        return {
            "message": "Successfully followed user",
            "follower_count": target_user.follower_count, # Returning target's new count might be useful, but wait, usually we want our own updated following count or target's new follower count. Let's return our counts or target counts. We will let the router format it.
        }

    @staticmethod
    async def unfollow_user(db: AsyncSession, follower_user: User, following_id: uuid.UUID) -> dict:
        """Unfollow another user."""
        stmt = select(Follow).where(and_(Follow.follower_id == follower_user.id, Follow.following_id == following_id))
        res = await db.execute(stmt)
        follow_record = res.scalar_one_or_none()
        
        if not follow_record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not following this user")

        # Load target user to update count
        stmt = select(User).where(User.id == following_id)
        res = await db.execute(stmt)
        target_user = res.scalar_one()

        await db.delete(follow_record)
        
        if target_user.follower_count > 0:
            target_user.follower_count -= 1
        if follower_user.following_count > 0:
            follower_user.following_count -= 1

        await db.commit()
        await db.refresh(follower_user)

        return {
            "message": "Successfully unfollowed user"
        }
