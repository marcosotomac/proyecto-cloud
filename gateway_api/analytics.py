import httpx
from typing import Optional, Dict, Any
from config import settings
from service_client import analytics_client
import logging
import time

logger = logging.getLogger(__name__)


async def track_analytics_event(
    service_type: str,
    event_type: str,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Track an analytics event (fire and forget)

    Args:
        service_type: Type of service (llm_chat, text_to_image, text_to_speech)
        event_type: Type of event (success, error, request)
        user_id: Optional user ID
        metadata: Optional event metadata
    """
    if not settings.ENABLE_ANALYTICS:
        return

    try:
        payload = {
            "service_type": service_type,
            "event_type": event_type,
            "metadata": metadata or {}
        }

        if user_id:
            payload["user_id"] = user_id

        # Fire and forget - don't wait for response
        response = await analytics_client.request(
            method="POST",
            endpoint="/analytics/track",
            json=payload
        )

        if response.status_code == 200:
            logger.debug(
                f"Analytics event tracked: {service_type} - {event_type}")
        else:
            logger.warning(
                f"Failed to track analytics event: {response.status_code}")

    except Exception as e:
        # Don't fail the main request if analytics fails
        logger.error(f"Analytics tracking error: {str(e)}")


class AnalyticsMiddleware:
    """Middleware to track request analytics"""

    def __init__(self, service_type: str):
        self.service_type = service_type

    async def track_request(
        self,
        user_id: Optional[str],
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track a service request"""
        event_type = "success" if success else "error"
        await track_analytics_event(
            service_type=self.service_type,
            event_type=event_type,
            user_id=user_id,
            metadata=metadata
        )
