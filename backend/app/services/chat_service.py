import uuid
import json
import logging
from typing import Dict, List, Optional
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.chat import Conversation, ConversationMember, Message, ConversationType
from app.models.user import User
from app.services.push_service import send_push_notification

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps user_id to a list of active WebSockets (if they have multiple devices/tabs open)
        self.active_connections: Dict[uuid.UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID):
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # Broadcast that this user is online
        await self.broadcast_user_status(user_id, "online")

    async def disconnect(self, websocket: WebSocket, user_id: uuid.UUID):
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # Broadcast that this user is offline
                await self.broadcast_user_status(user_id, "offline")

    async def send_personal_message(self, message: dict, user_id: uuid.UUID):
        """Send a JSON message to a specific user's active connections."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")

    async def broadcast_user_status(self, user_id: uuid.UUID, status: str):
        """Broadcast user status to everyone (or just friends, but we'll do everyone for simplicity)"""
        msg = {
            "type": "status",
            "user_id": str(user_id),
            "status": status
        }
        for u_id, connections in self.active_connections.items():
            if u_id != user_id:
                for connection in connections:
                    try:
                        await connection.send_json(msg)
                    except Exception:
                        pass

    def is_user_online(self, user_id: uuid.UUID) -> bool:
        return user_id in self.active_connections

manager = ConnectionManager()

async def get_user_conversations(db: AsyncSession, user_id: uuid.UUID) -> List[Conversation]:
    """Retrieve all conversations for a user, including the latest message."""
    stmt = (
        select(Conversation)
        .join(ConversationMember, Conversation.id == ConversationMember.conversation_id)
        .where(ConversationMember.user_id == user_id)
        .options(
            selectinload(Conversation.members).selectinload(ConversationMember.user),
            selectinload(Conversation.messages)  # Not ideal for huge chat history, but okay for a small list. We'll do a subquery later if needed.
        )
    )
    result = await db.execute(stmt)
    conversations = list(result.scalars().unique().all())
    
    # Sort messages and find the latest one, and calculate unread count
    for conv in conversations:
        conv.messages.sort(key=lambda m: m.created_at, reverse=True)
        conv.latest_message = conv.messages[0] if conv.messages else None
        
        member = next((m for m in conv.members if m.user_id == user_id), None)
        if member and member.last_read_at:
            conv.unread_count = sum(1 for m in conv.messages if m.created_at > member.last_read_at and m.sender_id != user_id)
        else:
            conv.unread_count = 0
        
    return conversations

async def create_direct_conversation(db: AsyncSession, user1_id: uuid.UUID, user2_id: uuid.UUID) -> Conversation:
   
    user1_convos_stmt = select(ConversationMember.conversation_id).where(ConversationMember.user_id == user1_id)
    result1 = await db.execute(user1_convos_stmt)
    user1_convos = [row[0] for row in result1.all()]

    if user1_convos:
        user2_convos_stmt = (
            select(Conversation)
            .join(ConversationMember, Conversation.id == ConversationMember.conversation_id)
            .where(Conversation.id.in_(user1_convos))
            .where(Conversation.type == ConversationType.direct)
            .where(ConversationMember.user_id == user2_id)
            .options(
                selectinload(Conversation.members).selectinload(ConversationMember.user)
            )
        )
        result2 = await db.execute(user2_convos_stmt)
        existing_conv = result2.scalar_one_or_none()
        if existing_conv:
            return existing_conv

    # Create new
    conv = Conversation(type=ConversationType.direct)
    db.add(conv)
    await db.flush()

    m1 = ConversationMember(conversation_id=conv.id, user_id=user1_id)
    m2 = ConversationMember(conversation_id=conv.id, user_id=user2_id)
    db.add_all([m1, m2])
    await db.commit()
    
    # Reload with members
    stmt = select(Conversation).where(Conversation.id == conv.id).options(
        selectinload(Conversation.members).selectinload(ConversationMember.user)
    )
    res = await db.execute(stmt)
    return res.scalar_one()

async def save_message_and_notify(db: AsyncSession, conversation_id: uuid.UUID, sender_id: uuid.UUID, content: str) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    
    # Load sender for the response
    stmt = select(User).where(User.id == sender_id)
    res = await db.execute(stmt)
    sender = res.scalar_one_or_none()
    msg.sender = sender

    # Find conversation members
    members_stmt = (
        select(ConversationMember)
        .options(selectinload(ConversationMember.user))
        .where(ConversationMember.conversation_id == conversation_id)
    )
    members_res = await db.execute(members_stmt)
    members = members_res.scalars().all()

    # Format the message payload
    payload = {
        "type": "new_message",
        "message": {
            "id": str(msg.id),
            "conversation_id": str(msg.conversation_id),
            "sender_id": str(msg.sender_id) if msg.sender_id else None,
            "content": msg.content,
            "is_system_message": msg.is_system_message,
            "created_at": msg.created_at.isoformat(),
            "sender": {
                "id": str(sender.id),
                "full_name": sender.full_name,
                "avatar": sender.avatar,
            } if sender else None
        }
    }

    sender_name = sender.full_name if sender else "Someone"

    # Send WebSocket message & Push Notification to others
    for m in members:
        if m.user_id != sender_id:
            # WebSocket
            await manager.send_personal_message(payload, m.user_id)
            
            # Push Notification if they are offline (or even if online)
            # For simplicity, we just send it. The frontend can suppress it if the app is foreground.
            if m.user and m.user.push_token:
                await send_push_notification(
                    push_token=m.user.push_token,
                    title=sender_name,
                    body=content,
                    data={"conversation_id": str(conversation_id)}
                )

    return msg
