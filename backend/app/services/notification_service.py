import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.auth import Notification, NotificationType
from app.services.chat_service import manager


class NotificationService:
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: uuid.UUID,
        title: str,
        body: str,
        notification_type: NotificationType,
        actor_id: Optional[uuid.UUID] = None,
        entity_id: Optional[str] = None
    ) -> Notification:
        """Create a notification in the DB and broadcast via WS."""
        notification = Notification(
            user_id=user_id,
            actor_id=actor_id,
            type=notification_type,
            title=title,
            body=body,
            entity_id=entity_id
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        # To send full actor details over WS, we can lazy load actor or query it
        # Actually since we just committed, we can load it:
        stmt = select(Notification).where(Notification.id == notification.id).options(selectinload(Notification.actor))
        res = await db.execute(stmt)
        notification = res.scalar_one()

        actor_data = None
        if notification.actor:
            actor_data = {
                "id": str(notification.actor.id),
                "full_name": notification.actor.full_name,
                "avatar": notification.actor.avatar
            }

        # Broadcast the notification
        payload = {
            "type": "new_notification",
            "notification": {
                "id": str(notification.id),
                "title": notification.title,
                "body": notification.body,
                "type": notification.type.value if hasattr(notification.type, 'value') else notification.type,
                "entity_id": notification.entity_id,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
                "actor": actor_data
            }
        }
        await manager.send_personal_message(payload, user_id)

        # Also broadcast unread count
        count_stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read == False
        )
        unread_count = await db.scalar(count_stmt)
        
        count_payload = {
            "type": "unread_count_update",
            "unread_count": unread_count or 0
        }
        await manager.send_personal_message(count_payload, user_id)

        return notification
