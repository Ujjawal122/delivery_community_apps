from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class GateBase(BaseModel):
    society_name: str = Field(..., max_length=255)
    address: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None

class GateCreate(GateBase):
    pass

class GateUpdate(BaseModel):
    society_name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None

class GateResponse(GateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class GateReviewBase(BaseModel):
    waiting_time: Optional[int] = None
    parking: Optional[bool] = None
    lift_available: Optional[bool] = None
    delivery_difficulty: Optional[int] = None
    guard_behavior: Optional[int] = None
    entry_restrictions: Optional[str] = None
    comment: Optional[str] = None
    overall_rating: Optional[int] = None

class GateReviewCreate(GateReviewBase):
    pass

class GateReviewUpdate(GateReviewBase):
    pass

class GateReviewResponse(GateReviewBase):
    id: UUID
    gate_id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
