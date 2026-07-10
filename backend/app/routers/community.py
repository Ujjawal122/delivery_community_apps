import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ApiResponse, created, ok
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.community import CommunityCreate
from app.services.community_service import CommunityService

router = APIRouter(tags=["Community Management"])

@router.post("/communities", response_model=ApiResponse, status_code=201,
             summary="Create a new community")
async def create_community(
    data: CommunityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await CommunityService.create_community(db, current_user, data)
    await db.commit()
    return created(result, "Community created successfully")

@router.get("/communities", response_model=ApiResponse,
            summary="List communities")
async def list_communities(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await CommunityService.list_communities(db, page, limit)
    return ok(result, "Communities retrieved")

@router.get("/communities/{community_id}", response_model=ApiResponse,
            summary="Get community details")
async def get_community(
    community_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await CommunityService.get_community(db, community_id)
    return ok(result, "Community retrieved")

@router.post("/communities/{community_id}/join", response_model=ApiResponse,
             summary="Join a community or request to join")
async def join_community(
    community_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await CommunityService.join_community(db, current_user, community_id)
    await db.commit()
    return ok(result, "Join processed")

@router.get("/communities/{community_id}/membership", response_model=ApiResponse,
            summary="Check membership status")
async def check_membership_status(
    community_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await CommunityService.check_membership_status(db, current_user, community_id)
    return ok(result, "Status retrieved")
