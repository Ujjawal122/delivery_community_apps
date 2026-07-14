from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.elements import WKTElement
from typing import List
import uuid

from app.core.responses import ApiResponse, ok, created
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.hazard import HazardReport
from app.schemas.hazard import HazardCreate, HazardResponse

router = APIRouter(prefix="/hazards", tags=["Hazards"])

@router.post("", response_model=ApiResponse, status_code=201, summary="Create a hazard report")
async def create_hazard(
    data: HazardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    point = f"POINT({data.longitude} {data.latitude})"
    new_hazard = HazardReport(
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        category_id=data.category_id,
        severity=data.severity,
        location=WKTElement(point, srid=4326),
        latitude=data.latitude,
        longitude=data.longitude,
    )
    db.add(new_hazard)
    await db.commit()
    await db.refresh(new_hazard)
    
    # Ideally add images logic here if HazardImage is used.
    
    return created(HazardResponse.model_validate(new_hazard).model_dump(mode="json"), "Hazard created successfully")

@router.get("", response_model=ApiResponse, summary="Get all hazards")
async def list_hazards(
    db: AsyncSession = Depends(get_db)
):
    stmt = select(HazardReport)
    result = await db.execute(stmt)
    hazards = result.scalars().all()
    
    return ok([HazardResponse.model_validate(h).model_dump(mode="json") for h in hazards], "Hazards retrieved")
