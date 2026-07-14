import httpx
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

async def send_push_notification(push_token: str, title: str, body: str, data: Optional[dict] = None) -> None:
    """
    Sends a push notification to an Expo push token.
    """
    if not push_token or not push_token.startswith("ExponentPushToken["):
        logger.warning(f"Invalid push token: {push_token}")
        return

    payload = {
        "to": push_token,
        "title": title,
        "body": body,
        "data": data or {},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(EXPO_PUSH_URL, json=payload, timeout=5.0)
            if response.status_code != 200:
                logger.error(f"Failed to send push notification: {response.text}")
    except Exception as e:
        logger.error(f"Exception sending push notification: {e}")

async def send_push_notifications(messages: List[dict]) -> None:
    """
    Sends multiple push notifications. messages = [{"to": token, "title": title, "body": body, "data": {}}]
    """
    valid_messages = [
        msg for msg in messages 
        if msg.get("to") and str(msg["to"]).startswith("ExponentPushToken[")
    ]
    if not valid_messages:
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(EXPO_PUSH_URL, json=valid_messages, timeout=10.0)
            if response.status_code != 200:
                logger.error(f"Failed to send push notifications: {response.text}")
    except Exception as e:
        logger.error(f"Exception sending push notifications: {e}")
