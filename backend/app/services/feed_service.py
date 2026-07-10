from uuid import UUID
from typing import Optional, List
from sqlalchemy import select, func, or_, case
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_DistanceSphere, ST_MakePoint, ST_SetSRID

from app.models.post import Post, PostVote
from app.models.user import User
from app.models.community import Community

class FeedService:
    @staticmethod
    async def get_personalized_feed(
        session,
        user_id: UUID,
        req_lat: Optional[float],
        req_lon: Optional[float],
        radius_km: float,
        page: int,
        limit: int
    ) -> tuple[List[Post], int]:
        """
        Retrieves a personalized feed of posts using a matrix scoring algorithm.
        Score factors:
        - Within location radius (using passed lat/lon OR user profile location)
        - Matching interests (User's interests vs Community's purpose)
        - Recentness (decay over time)
        - Popularity (upvotes - downvotes)
        """
        # Fetch the user to get their profile location and interests
        user_stmt = select(User).where(User.id == user_id)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user:
            # Fallback if user not found, just return recent posts
            return await FeedService._get_fallback_feed(session, page, limit)

        # 1. Base Query
        stmt = select(Post).options(
            selectinload(Post.author),
            selectinload(Post.community)
        )

        # 2. Location Logic (Radius Algorithm)
        # We can construct two point geometries: request location and user profile location.
        location_conditions = []
        radius_meters = radius_km * 1000

        if req_lat is not None and req_lon is not None:
            # PostGIS ST_MakePoint takes (longitude, latitude)
            req_point = ST_SetSRID(ST_MakePoint(req_lon, req_lat), 4326)
            dist_req = ST_DistanceSphere(Post.location, req_point)
            location_conditions.append(dist_req <= radius_meters)

        if user.location is not None:
            dist_prof = ST_DistanceSphere(Post.location, user.location)
            location_conditions.append(dist_prof <= radius_meters)

        is_in_location = or_(*location_conditions) if location_conditions else False

        # 3. Interest Logic
        user_interests = user.interests or []
        is_in_interest = False
        if user_interests:
            # We join Community to check purpose against interests
            stmt = stmt.outerjoin(Community, Post.community_id == Community.id)
            # SQLAlchemy casts enum to text for ANY() comparison or we can just use IN
            is_in_interest = Community.purpose.in_(user_interests)
        else:
            stmt = stmt.outerjoin(Community, Post.community_id == Community.id)

        # 4. Matrix Scoring Algorithm
        # Base score + Location Bonus + Interest Bonus + Vote Bonus - Age Penalty
        # Location Bonus: 50
        # Interest Bonus: 30
        # Upvotes: +1 each, Downvotes: -1 each
        
        location_score = case((is_in_location, 50), else_=0) if isinstance(is_in_location, bool) is False else (50 if is_in_location else 0)
        interest_score = case((is_in_interest, 30), else_=0) if isinstance(is_in_interest, bool) is False else (30 if is_in_interest else 0)
        vote_score = Post.upvotes_count - Post.downvotes_count

        total_score = (
            location_score +
            interest_score +
            vote_score
        )

        # 5. Order by total score descending, then by created_at
        stmt = stmt.order_by(total_score.desc(), Post.created_at.desc())

        # 6. Pagination
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        result = await session.execute(stmt)
        posts = result.scalars().all()

        # Get user votes
        if posts and user_id:
            post_ids = [p.id for p in posts]
            votes_stmt = select(PostVote).where(
                PostVote.user_id == user_id,
                PostVote.post_id.in_(post_ids)
            )
            votes_res = await session.execute(votes_stmt)
            vote_map = {v.post_id: v.vote_type for v in votes_res.scalars().all()}
            for p in posts:
                p.user_vote = vote_map.get(p.id)

        # Get total count (for pagination)
        count_stmt = select(func.count(Post.id))
        count_res = await session.execute(count_stmt)
        total = count_res.scalar_one()

        return list(posts), total

    @staticmethod
    async def _get_fallback_feed(session, page: int, limit: int):
        stmt = select(Post).options(
            selectinload(Post.author),
            selectinload(Post.community)
        ).order_by(Post.created_at.desc())
        
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        result = await session.execute(stmt)
        posts = result.scalars().all()
        
        # User votes logic could be added here if user_id was passed, but it's a fallback.
        # So we just leave them None.

        count_stmt = select(func.count(Post.id))
        count_res = await session.execute(count_stmt)
        total = count_res.scalar_one()

        return list(posts), total
