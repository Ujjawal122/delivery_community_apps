import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.websockets import WebSocketState

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message, ConversationMember
from app.schemas.chat import (
    ConversationResponse, 
    MessageResponse, 
    MessageCreate, 
    CreateDirectConversationRequest
)
from app.services.chat_service import (
    manager, 
    get_user_conversations, 
    create_direct_conversation, 
    save_message_and_notify
)
from app.services.jwt_service import JWTService
from app.services.follow_service import FollowService
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations for the current user."""
    return await get_user_conversations(db, current_user.id)


@router.post("/conversations/direct", response_model=ConversationResponse)
async def create_direct_chat(
    req: CreateDirectConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or get a direct conversation with another user."""
    if current_user.id == req.target_user_id:
        raise HTTPException(status_code=400, detail="Cannot chat with yourself.")
    
    target_user = await UserRepository(db).get_by_id(req.target_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found.")
        
    is_mutual = await FollowService.is_mutual_follower(db, current_user.id, req.target_user_id)
    if not is_mutual:
        raise HTTPException(status_code=403, detail="You can chat after both users follow each other.")
        
    return await create_direct_conversation(db, current_user.id, req.target_user_id)


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages for a specific conversation."""
    # Check if user is a member
    member_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == current_user.id
    )
    member_res = await db.execute(member_stmt)
    if not member_res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this conversation.")
        
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .options(selectinload(Message.sender))
        .order_by(Message.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(stmt)
    messages = list(res.scalars().all())
    messages.reverse()  # chronological order
    return messages


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: uuid.UUID,
    msg_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a REST message if WebSocket is not available."""
    # Check if user is a member
    member_stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == current_user.id
    )
    member_res = await db.execute(member_stmt)
    if not member_res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this conversation.")
        
    return await save_message_and_notify(db, conversation_id, current_user.id, msg_data.content)


@router.post("/conversations/{conversation_id}/read", response_model=dict)
async def mark_conversation_read(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime, timezone
    stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this conversation.")
        
    member.last_read_at = datetime.now(timezone.utc)
    await db.commit()
    return {"success": True}

# --- WebSocket Endpoint ---

@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """
    WebSocket endpoint for real-time chat.
    The client must send an initial authentication message with their JWT token.
    """
    await websocket.accept()
    
    # Wait for authentication message
    try:
        data = await websocket.receive_json()
        if data.get("type") != "auth" or not data.get("token"):
            await websocket.close(code=1008, reason="Missing or invalid authentication")
            return
            
        token = data["token"]
        payload = JWTService.decode_token_safe(token, expected_type="access")
        if not payload or "sub" not in payload:
            await websocket.close(code=1008, reason="Invalid token")
            return
            
        user_id_str = payload["sub"]
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            await websocket.close(code=1008, reason="Invalid user ID")
            return
            
    except WebSocketDisconnect:
        return
    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        await websocket.close(code=1008, reason="Internal error")
        return

    # User is authenticated
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "typing":
                # Broadcast typing status to the conversation
                conv_id_str = data.get("conversation_id")
                if not conv_id_str:
                    continue
                try:
                    conv_id = uuid.UUID(conv_id_str)
                except ValueError:
                    continue
                    
                typing_payload = {
                    "type": "typing",
                    "conversation_id": str(conv_id),
                    "user_id": str(user_id)
                }
                
                # Fetch members and forward
                members_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == conv_id)
                members_res = await db.execute(members_stmt)
                member_ids = members_res.scalars().all()
                for m_id in member_ids:
                    if m_id != user_id:
                        await manager.send_personal_message(typing_payload, m_id)

    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket unexpected error: {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await manager.disconnect(websocket, user_id)
