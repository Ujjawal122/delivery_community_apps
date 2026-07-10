from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from app.core.responses import ApiResponse, ok
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.gate import LocationUpdate
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["Locations"])

@router.post("/update", response_model=ApiResponse, summary="Update background location")
async def update_location(
    data: LocationUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Called periodically by the frontend in the background to update location
    and check for nearby hazards or gates.
    """
    result = await LocationService.update_location_and_check_proximity(
        db, current_user, data.latitude, data.longitude, radius_meters=500.0
    )
    await db.commit()
    return ok(result, "Location updated and checked")


@router.post("/push-token", response_model=ApiResponse, summary="Register push token")
async def register_push_token(
    push_token: str = Query(..., description="The Expo Push Token"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Registers the user's device for Push Notifications.
    """
    await LocationService.update_user_push_token(db, current_user, push_token)
    await db.commit()
    return ok(None, "Push token registered successfully")
