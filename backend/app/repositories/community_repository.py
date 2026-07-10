import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.community import Community, CommunityMember
from app.repositories.base import BaseRepository


class CommunityRepository(BaseRepository[Community]):
    model = Community

    async def create(
        self,
        *,
        name: str,
        unique_name: str,
        purpose: str,
        is_public: bool,
        about: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> Community:
        community = Community(
            name=name,
            unique_name=unique_name,
            purpose=purpose,
            is_public=is_public,
            about=about,
            created_by=created_by,
        )
        self.add(community)
        await self.flush()
        
        # Add creator as a member
        if created_by:
            member = CommunityMember(user_id=created_by, community_id=community.id)
            self.db.add(member)
            await self.flush()

        await self.refresh(community)
        return community

    async def list_communities(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Community]:
        result = await self.db.execute(
            select(Community)
            .order_by(Community.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_member(self, community_id: uuid.UUID, user_id: uuid.UUID) -> Optional[CommunityMember]:
        result = await self.db.execute(
            select(CommunityMember)
            .where(CommunityMember.community_id == community_id)
            .where(CommunityMember.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add_member(self, community_id: uuid.UUID, user_id: uuid.UUID) -> CommunityMember:
        member = CommunityMember(user_id=user_id, community_id=community_id)
        self.db.add(member)
        await self.flush()
        return member

    async def get_join_request(self, community_id: uuid.UUID, user_id: uuid.UUID):
        from app.models.community import CommunityJoinRequest
        result = await self.db.execute(
            select(CommunityJoinRequest)
            .where(CommunityJoinRequest.community_id == community_id)
            .where(CommunityJoinRequest.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_join_request(self, community_id: uuid.UUID, user_id: uuid.UUID):
        from app.models.community import CommunityJoinRequest, JoinRequestStatus
        req = CommunityJoinRequest(user_id=user_id, community_id=community_id, status=JoinRequestStatus.pending)
        self.db.add(req)
        await self.flush()
        return req
