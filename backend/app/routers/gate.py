from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.elements import WKTElement
from typing import List
import uuid

from app.core.responses import ApiResponse, ok, created
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.gate import Gate, GateReview
from app.schemas.gate import GateCreate, GateResponse, GateReviewCreate, GateReviewResponse

router = APIRouter(prefix="/gates", tags=["Gates"])

@router.post("", response_model=ApiResponse, status_code=201, summary="Create a gate")
async def create_gate(
    data: GateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    point = None
    if data.longitude is not None and data.latitude is not None:
        point = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)

    new_gate = Gate(
        society_name=data.society_name,
        address=data.address,
        location=point,
    )
    db.add(new_gate)
    await db.commit()
    await db.refresh(new_gate)
    
    return created(GateResponse.model_validate(new_gate).model_dump(mode="json"), "Gate created successfully")

@router.get("", response_model=ApiResponse, summary="Get all gates")
async def list_gates(
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Gate)
    result = await db.execute(stmt)
    gates = result.scalars().all()
    
    return ok([GateResponse.model_validate(g).model_dump(mode="json") for g in gates], "Gates retrieved")

@router.post("/{gate_id}/reviews", response_model=ApiResponse, status_code=201, summary="Submit a gate review")
async def submit_gate_review(
    gate_id: uuid.UUID,
    data: GateReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_review = GateReview(
        gate_id=gate_id,
        user_id=current_user.id,
        waiting_time=data.waiting_time,
        parking=data.parking,
        lift_available=data.lift_available,
        delivery_difficulty=data.delivery_difficulty,
        guard_behavior=data.guard_behavior,
        entry_restrictions=data.entry_restrictions,
        comment=data.comment,
        overall_rating=data.overall_rating
    )
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    
    return created(GateReviewResponse.model_validate(new_review).model_dump(mode="json"), "Review submitted")

@router.get("/{gate_id}/reviews", response_model=ApiResponse, summary="Get gate reviews")
async def list_gate_reviews(
    gate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(GateReview).where(GateReview.gate_id == gate_id)
    result = await db.execute(stmt)
    reviews = result.scalars().all()
    
    return ok([GateReviewResponse.model_validate(r).model_dump(mode="json") for r in reviews], "Gate reviews retrieved")
