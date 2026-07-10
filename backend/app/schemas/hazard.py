from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

class HazardSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class HazardStatus(str, Enum):
    pending = "pending"
    resolved = "resolved"
    rejected = "rejected"

class HazardBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    category_id: Optional[int] = None
    severity: HazardSeverity = HazardSeverity.medium
    latitude: float
    longitude: float

class HazardCreate(HazardBase):
    images: Optional[List[str]] = None

class HazardUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category_id: Optional[int] = None
    severity: Optional[HazardSeverity] = None
    status: Optional[HazardStatus] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class HazardResponse(HazardBase):
    id: UUID
    user_id: UUID
    status: HazardStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HazardImageResponse(BaseModel):
    id: UUID
    hazard_id: UUID
    image_url: str
    created_at: datetime

    class Config:
        from_attributes = True
