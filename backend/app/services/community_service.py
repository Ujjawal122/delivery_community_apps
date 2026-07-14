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
        community.creator = current_user
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
            
            # Send notification to the community creator
            if community.created_by:
                from app.services.notification_service import NotificationService
                from app.models.auth import NotificationType
                await NotificationService.create_notification(
                    db=db,
                    user_id=community.created_by,
                    title="New Join Request",
                    body=f"{current_user.full_name} wants to join {community.name}.",
                    notification_type=NotificationType.community_join_request,
                    actor_id=current_user.id,
                    entity_id=str(community_id)
                )
            
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
        
    @staticmethod
    async def handle_join_request(db: AsyncSession, current_user: User, community_id: uuid.UUID, target_user_id: uuid.UUID, action: str):
        repo = CommunityRepository(db)
        community = await repo.get_by_id(community_id)
        if not community:
            raise NotFoundError("Community not found")
            
        # Verify the current_user is the creator or admin
        if community.created_by != current_user.id:
            raise Exception("Only community creators can approve or reject join requests.")
            
        req = await repo.get_join_request(community_id, target_user_id)
        current_status = req.status.value if hasattr(req.status, 'value') else req.status if req else None
        if not req or current_status != "pending":
            raise Exception("Join request not found or already processed.")
            
        if action == "approve":
            await repo.update_join_request_status(community_id, target_user_id, "approved")
            await repo.add_member(community_id, target_user_id)
            
            from app.services.notification_service import NotificationService
            from app.models.auth import NotificationType
            await NotificationService.create_notification(
                db=db,
                user_id=target_user_id,
                title="Join Request Approved",
                body=f"Your request to join {community.name} was approved.",
                notification_type=NotificationType.community_approved,
                actor_id=current_user.id,
                entity_id=str(community_id)
            )
            return {"status": "approved"}
        elif action == "reject":
            await repo.update_join_request_status(community_id, target_user_id, "rejected")
            
            from app.services.notification_service import NotificationService
            from app.models.auth import NotificationType
            await NotificationService.create_notification(
                db=db,
                user_id=target_user_id,
                title="Join Request Rejected",
                body=f"Your request to join {community.name} was rejected.",
                notification_type=NotificationType.community_rejected,
                actor_id=current_user.id,
                entity_id=str(community_id)
            )
            return {"status": "rejected"}
        else:
            raise ValueError("Invalid action")
