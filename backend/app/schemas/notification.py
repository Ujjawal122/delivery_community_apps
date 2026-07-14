from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.auth import NotificationType


class NotificationActor(BaseModel):
    id: UUID
    full_name: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: UUID
    title: str
    body: str
    type: NotificationType
    entity_id: Optional[str] = None
    is_read: bool
    created_at: datetime
    
    actor: Optional[NotificationActor] = None

    class Config:
        from_attributes = True


class NotificationPaginated(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    size: int


class UnreadCountResponse(BaseModel):
    unread_count: int
