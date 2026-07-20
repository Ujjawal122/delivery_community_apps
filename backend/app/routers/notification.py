from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.auth import Notification
from app.schemas.notification import NotificationPaginated, UnreadCountResponse
from app.core.responses import ApiResponse, ok

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=ApiResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    
    # Query for notifications, include the actor info if exists
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
        .offset(offset)
    )
    
    # We should eager load the actor relationship or just rely on async lazy load / joinedload
    from sqlalchemy.orm import selectinload
    stmt = stmt.options(selectinload(Notification.actor))
    
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    
    count_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == current_user.id)
    total = await db.scalar(count_stmt)
    
    from app.models.community import CommunityJoinRequest
    from app.models.auth import NotificationType
    
    items = []
    for n in notifications:
        actor_data = None
        if n.actor:
            actor_data = {
                "id": n.actor.id,
                "full_name": n.actor.full_name,
                "avatar": n.actor.avatar
            }
            
        extra_data = None
        if n.type == NotificationType.community_join_request:
            if n.entity_id and n.actor_id:
                try:
                    stmt_req = select(CommunityJoinRequest.status).where(
                        CommunityJoinRequest.community_id == UUID(n.entity_id),
                        CommunityJoinRequest.user_id == n.actor_id
                    )
                    req_status = await db.scalar(stmt_req)
                    if req_status:
                        extra_data = {"request_status": req_status.value}
                except Exception:
                    pass
                    
        items.append({
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "type": n.type,
            "entity_id": n.entity_id,
            "is_read": n.is_read,
            "created_at": n.created_at,
            "extra_data": extra_data,
            "actor": actor_data
        })
        
    return ok(
        {
            "items": items,
            "total": total,
            "page": page,
            "size": len(items)
        },
        "Notifications retrieved successfully"
    )


@router.get("/unread-count", response_model=ApiResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(func.count()).select_from(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    count = await db.scalar(stmt)
    return ok({"unread_count": count or 0}, "Unread count retrieved")


@router.patch("/{notification_id}/read", response_model=ApiResponse)
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    )
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notification.is_read = True
    await db.commit()
    
    return ok(None, "Notification marked as read")


@router.post("/mark-all-read", response_model=ApiResponse)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import update
    stmt = (
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .where(Notification.is_read == False)
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.commit()
    
    return ok(None, "All notifications marked as read")


@router.delete("/{notification_id}", response_model=ApiResponse)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    )
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    await db.delete(notification)
    await db.commit()
    
    return ok(None, "Notification deleted")
