

import math
from datetime import datetime, timezone, timedelta
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape

from app.models.user import User
from app.models.hazard import HazardReport, HazardStatus
from app.models.gate import Gate
from app.schemas.hazard import HazardResponse
from app.schemas.gate import GateResponse
from app.core.logging import get_logger
from app.services.push_service import send_push_notifications  # Bug #4 fix

logger = get_logger(__name__)

# Cooldown: only re-notify the same (user, hazard) pair after this duration
NOTIFICATION_COOLDOWN_MINUTES = 10

# In-memory cooldown store: (user_id, hazard_id) -> datetime of last notification
# For a production system, replace with Redis or a DB table.
_last_notified: dict[tuple, datetime] = {}


def _haversine_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine formula — accurate great-circle distance in metres."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _should_notify(user_id: str, hazard_id: str) -> bool:
    """Bug #1 fix: Returns True only if cooldown has expired or first time."""
    key = (user_id, str(hazard_id))
    last = _last_notified.get(key)
    if last is None:
        return True
    elapsed = datetime.now(timezone.utc) - last
    if elapsed >= timedelta(minutes=NOTIFICATION_COOLDOWN_MINUTES):
        return True
    remaining = NOTIFICATION_COOLDOWN_MINUTES * 60 - elapsed.seconds
    logger.info(
        f"[HazardAlert] ⏭️ Notification skipped (cooldown). "
        f"user={user_id} hazard={hazard_id} — {remaining}s remaining"
    )
    return False


def _mark_notified(user_id: str, hazard_id: str):
    key = (user_id, str(hazard_id))
    _last_notified[key] = datetime.now(timezone.utc)


class LocationService:

    @staticmethod
    async def update_user_push_token(db: AsyncSession, user: User, push_token: str):
        """Registers or updates the user's Expo push token."""
        logger.info(f"[HazardAlert] 🎫 Updating push token for user {user.id}")
        user.push_token = push_token
        db.add(user)

    @staticmethod
    async def update_location_and_check_proximity(
        db: AsyncSession,
        user: User,
        latitude: float,
        longitude: float,
        radius_meters: float = 500.0,
    ) -> dict:
        """
        1. Updates user's stored location.
        2. Queries nearby hazards via PostGIS ST_DWithin.
        3. Sends push notifications — with deduplication (Bug #1 fix).
        4. Returns full proximity data including distances for the debug screen.
        """
        logger.info(
            f"[HazardAlert] 📍 Location update — user={user.id} "
            f"lat={latitude:.6f} lon={longitude:.6f} radius={radius_meters}m"
        )

        # 1. Persist user location
        point_wkt = f"POINT({longitude} {latitude})"
        user.location = WKTElement(point_wkt, srid=4326)
        user.latitude = latitude
        user.longitude = longitude
        db.add(user)

        # 2. Query nearby hazards
        hazards = await LocationService.get_nearby_hazards(db, latitude, longitude, radius_meters)
        gates = await LocationService.get_nearby_gates(db, latitude, longitude, radius_meters)

        logger.info(f"[HazardAlert] 🔍 Found {len(hazards)} hazard(s), {len(gates)} gate(s) within {radius_meters}m")

        # 3. Build notifications with dedup
        notifications_sent = 0
        hazard_details = []

        if user.push_token:
            messages = []
            for h in hazards:
                # Calculate precise Haversine distance for message personalisation
                h_lat, h_lon = LocationService._extract_coords(h.location)
                dist_m = int(_haversine_metres(latitude, longitude, h_lat, h_lon))

                inside = dist_m <= radius_meters
                notify = inside and _should_notify(str(user.id), str(h.id))

                if notify:
                    dist_text = f"{dist_m} metres" if dist_m < 1000 else f"{dist_m / 1000:.1f} km"
                    body = f"⚠️ {h.title} reported {dist_text} ahead."
                    messages.append({
                        "to": user.push_token,
                        "title": "Hazard Alert",
                        "body": body,
                        "data": {"type": "hazard", "hazard_id": str(h.id), "distance_m": dist_m},
                        "sound": "default",
                    })
                    _mark_notified(str(user.id), str(h.id))
                    logger.info(f"[HazardAlert] ✅ Queued notification for hazard '{h.title}' ({dist_m}m)")
                elif inside:
                    logger.info(f"[HazardAlert] ⏭️ Skipped duplicate for hazard '{h.title}'")
                else:
                    logger.info(f"[HazardAlert] ⬜ Hazard '{h.title}' outside radius ({dist_m}m > {radius_meters}m)")

                hazard_details.append({
                    **HazardResponse.model_validate(h).model_dump(mode="json"),
                    "distance_m": dist_m,
                    "inside_radius": inside,
                    "notification_sent": notify,
                })

            for g in gates:
                g_lat, g_lon = LocationService._extract_coords(g.location)
                dist_m = int(_haversine_metres(latitude, longitude, g_lat, g_lon))
                if _should_notify(str(user.id), f"gate_{g.id}"):
                    messages.append({
                        "to": user.push_token,
                        "title": "Gate Nearby",
                        "body": f"Approaching {g.society_name} gate ({dist_m}m).",
                        "data": {"type": "gate", "gate_id": str(g.id), "distance_m": dist_m},
                    })
                    _mark_notified(str(user.id), f"gate_{g.id}")

            # Bug #4 fix: use push_service instead of inline httpx
            if messages:
                await send_push_notifications(messages)
                notifications_sent = len(messages)
                logger.info(f"[HazardAlert] 🔔 Sent {notifications_sent} push notification(s)")

        return {
            "hazards": hazard_details,
            "gates": [GateResponse.model_validate(g).model_dump(mode="json") for g in gates],
            "notifications_sent": notifications_sent,
            "user_lat": latitude,
            "user_lon": longitude,
            "radius_meters": radius_meters,
        }

    @staticmethod
    def _extract_coords(geom) -> Tuple[float, float]:
        """Extracts (lat, lon) from a GeoAlchemy2 geometry column."""
        try:
            shape = to_shape(geom)
            return shape.y, shape.x  # lat, lon
        except Exception:
            return 0.0, 0.0

    @staticmethod
    async def get_nearby_hazards(
        db: AsyncSession, latitude: float, longitude: float, radius_meters: float = 500.0
    ) -> List[HazardReport]:
        """Fetch active hazards within the given radius using PostGIS ST_DWithin."""
        point = WKTElement(f"POINT({longitude} {latitude})", srid=4326)
        stmt = (
            select(HazardReport)
            .where(HazardReport.status == HazardStatus.pending)
            .where(func.ST_DWithin(HazardReport.location, point, radius_meters, True))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_nearby_gates(
        db: AsyncSession, latitude: float, longitude: float, radius_meters: float = 500.0
    ) -> List[Gate]:
        """Fetch gates within the given radius using PostGIS ST_DWithin."""
        point = WKTElement(f"POINT({longitude} {latitude})", srid=4326)
        stmt = (
            select(Gate)
            .where(func.ST_DWithin(Gate.location, point, radius_meters, True))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
