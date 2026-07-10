import uuid
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.community_repository import CommunityRepository
from app.schemas.community import CommunityCreate, CommunityResponse


class CommunityService:
    @staticmethod
    async def create_community(
        db: AsyncSession,
        current_user: User,
        data: CommunityCreate,
    ) -> CommunityResponse:
        repo = CommunityRepository(db)
        
        # Hash the name to create unique_name
        unique_name = hashlib.md5(f"{data.name}-{uuid.uuid4()}".encode()).hexdigest()

        community = await repo.create(
            name=data.name,
            unique_name=unique_name,
            purpose=data.purpose,
            is_public=data.is_public,
            about=data.about,
            created_by=current_user.id,
        )
        return CommunityResponse.model_validate(community)

    @staticmethod
    async def get_community(db: AsyncSession, community_id: uuid.UUID) -> CommunityResponse:
        repo = CommunityRepository(db)
        community = await repo.get_by_id(community_id)
        if not community:
            raise NotFoundError("Community not found")
        return CommunityResponse.model_validate(community)

    @staticmethod
    async def list_communities(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
    ) -> list[CommunityResponse]:
        repo = CommunityRepository(db)
        offset = (page - 1) * limit
        communities = await repo.list_communities(offset, limit)
        return [CommunityResponse.model_validate(c) for c in communities]

    @staticmethod
    async def join_community(db: AsyncSession, current_user: User, community_id: uuid.UUID):
        repo = CommunityRepository(db)
        community = await repo.get_by_id(community_id)
        if not community:
            raise NotFoundError("Community not found")

        # Check if already member
        member = await repo.get_member(community_id, current_user.id)
        if member:
            return {"status": "joined"}

        if community.is_public:
            await repo.add_member(community_id, current_user.id)
            return {"status": "joined"}
        else:
            # Check existing request
            req = await repo.get_join_request(community_id, current_user.id)
            if req:
                return {"status": req.status.value}
            
            await repo.create_join_request(community_id, current_user.id)
            return {"status": "pending"}

    @staticmethod
    async def check_membership_status(db: AsyncSession, current_user: User, community_id: uuid.UUID):
        repo = CommunityRepository(db)
        community = await repo.get_by_id(community_id)
        if not community:
            raise NotFoundError("Community not found")
            
        member = await repo.get_member(community_id, current_user.id)
        if member:
            return {"is_member": True, "role": member.role.value, "join_request_status": None}
            
        req = await repo.get_join_request(community_id, current_user.id)
        req_status = req.status.value if req else None
        
        return {"is_member": False, "role": None, "join_request_status": req_status}
