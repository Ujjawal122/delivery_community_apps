import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional
from app.models.chat import ConversationType
from app.schemas.user import UserResponse

class MessageCreate(BaseModel):
    content: str
    is_system_message: bool = False

class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: Optional[uuid.UUID]
    content: str
    is_system_message: bool
    created_at: datetime
    updated_at: datetime
    
    sender: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationMemberResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    last_read_at: datetime
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: uuid.UUID
    type: ConversationType
    community_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    
    members: List[ConversationMemberResponse] = []
    # We may include the latest message for the chat list view
    latest_message: Optional[MessageResponse] = None

    model_config = ConfigDict(from_attributes=True)


class CreateDirectConversationRequest(BaseModel):
    target_user_id: uuid.UUID

