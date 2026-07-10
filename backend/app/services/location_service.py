import httpx
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.elements import WKTElement
import uuid

from app.models.user import User
from app.models.hazard import HazardReport, HazardStatus
from app.models.gate import Gate
from app.schemas.hazard import HazardResponse
from app.schemas.gate import GateResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

class LocationService:
    @staticmethod
    async def update_user_push_token(db: AsyncSession, user: User, push_token: str):
        """Update the user's push notification token."""
        user.push_token = push_token
        db.add(user)
        # Commit happens in the router

    @staticmethod
    async def update_location_and_check_proximity(
        db: AsyncSession, 
        user: User, 
        latitude: float, 
        longitude: float, 
        radius_meters: float = 500.0
    ) -> dict:
        """
        Updates the user's location and checks for nearby hazards or gates.
        If found and the user has a push token, sends a push notification.
        """
        # 1. Update User Location
        point = f"POINT({longitude} {latitude})"
        user.location = WKTElement(point, srid=4326)
        db.add(user)
        
        # 2. Check for nearby Hazards
        hazards = await LocationService.get_nearby_hazards(db, latitude, longitude, radius_meters)
        
        # 3. Check for nearby Gates
        gates = await LocationService.get_nearby_gates(db, latitude, longitude, radius_meters)
        
        # 4. Trigger Push Notification (only if they have a token)
        # In a real system, you'd want to track which notifications were already sent 
        # to avoid spamming the user every time their location updates within the radius.
        # For simplicity, we just check if there are ANY nearby.
        
        notifications_sent = 0
        if user.push_token:
            messages = []
            for h in hazards:
                messages.append({
                    "to": user.push_token,
                    "title": "Hazard Nearby!",
                    "body": f"You are within {radius_meters}m of a reported hazard: {h.title}",
                    "data": {"type": "hazard", "id": str(h.id)}
                })
            
            for g in gates:
                messages.append({
                    "to": user.push_token,
                    "title": "Gate Nearby",
                    "body": f"You are approaching the gate for {g.society_name}.",
                    "data": {"type": "gate", "id": str(g.id)}
                })
            
            # Send notifications (consider running this as a background task via Celery/FastAPI BackgroundTasks)
            if messages:
                async with httpx.AsyncClient() as client:
                    try:
                        resp = await client.post(EXPO_PUSH_URL, json=messages)
                        logger.info(f"Sent {len(messages)} push notifications. Response: {resp.status_code}")
                        notifications_sent = len(messages)
                    except Exception as e:
                        logger.error(f"Error sending push notification: {e}")

        return {
            "hazards": [HazardResponse.model_validate(h) for h in hazards],
            "gates": [GateResponse.model_validate(g) for g in gates],
            "notifications_sent": notifications_sent
        }

    @staticmethod
    async def get_nearby_hazards(db: AsyncSession, latitude: float, longitude: float, radius_meters: float = 500.0) -> List[HazardReport]:
        """Fetch active hazards within the given radius in meters."""
        point = WKTElement(f"POINT({longitude} {latitude})", srid=4326)
        
        stmt = (
            select(HazardReport)
            .where(HazardReport.status == HazardStatus.pending)
            .where(func.ST_DWithin(HazardReport.location, point, radius_meters, use_spheroid=True))
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_nearby_gates(db: AsyncSession, latitude: float, longitude: float, radius_meters: float = 500.0) -> List[Gate]:
        """Fetch gates within the given radius in meters."""
        point = WKTElement(f"POINT({longitude} {latitude})", srid=4326)
        
        stmt = (
            select(Gate)
            .where(func.ST_DWithin(Gate.location, point, radius_meters, use_spheroid=True))
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
