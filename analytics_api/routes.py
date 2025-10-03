from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
import uuid
import logging

from models import (
    TrackEventRequest,
    TrackEventResponse,
    UserAnalyticsResponse,
    ServiceAnalyticsResponse,
    SystemAnalyticsResponse,
    UsageStatsResponse,
    HealthResponse,
    ServiceType,
    EventType,
    TimeRange
)
from db import db
from auth import get_current_user, require_auth

logger = logging.getLogger(__name__)

router = APIRouter()

# ============= Health Check =============


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await db.events_collection.find_one()
        return HealthResponse(database="connected")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(database="disconnected", status="unhealthy")

# ============= Event Tracking =============


@router.post("/analytics/track", response_model=TrackEventResponse, tags=["Events"])
async def track_event(
    request: TrackEventRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Track an analytics event

    This endpoint is typically called by other microservices to log usage events.
    Can be called with or without authentication.
    """
    try:
        # Generate event ID
        event_id = str(uuid.uuid4())

        # Get user ID from auth or request
        user_id = None
        if current_user:
            user_id = current_user.get("userId")
        elif request.user_id:
            user_id = request.user_id

        # Prepare event data
        event_data = {
            "event_id": event_id,
            "user_id": user_id,
            "service_type": request.service_type.value,
            "event_type": request.event_type.value,
            "timestamp": datetime.utcnow(),
            "metadata": request.metadata
        }

        # Store in database
        await db.track_event(event_data)

        logger.info(
            f"Tracked {request.event_type.value} event for service {request.service_type.value}")

        return TrackEventResponse(
            event_id=event_id,
            timestamp=event_data["timestamp"]
        )

    except Exception as e:
        logger.error(f"Failed to track event: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to track event: {str(e)}")

# ============= User Analytics =============


@router.get("/analytics/user", response_model=UserAnalyticsResponse, tags=["Analytics"])
async def get_user_analytics(
    user_id: Optional[str] = Query(
        None, description="User ID (leave empty for current user)"),
    time_range: TimeRange = Query(
        TimeRange.ALL, description="Time range for analytics"),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get analytics for a specific user

    - If user_id is not provided and user is authenticated, returns analytics for current user
    - If user_id is not provided and user is not authenticated, returns analytics for anonymous users
    - Admin users can query any user_id
    """
    try:
        # Determine which user to query
        query_user_id = user_id
        if query_user_id is None and current_user:
            query_user_id = current_user.get("userId")

        # Get analytics data
        analytics_data = await db.get_user_analytics(query_user_id, time_range)

        return UserAnalyticsResponse(
            user_id=query_user_id,
            **analytics_data
        )

    except Exception as e:
        logger.error(f"Failed to get user analytics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/analytics/user/me", response_model=UserAnalyticsResponse, tags=["Analytics"])
async def get_my_analytics(
    time_range: TimeRange = Query(
        TimeRange.ALL, description="Time range for analytics"),
    current_user: dict = Depends(require_auth)
):
    """
    Get analytics for the current authenticated user (requires authentication)
    """
    try:
        user_id = current_user.get("userId")
        analytics_data = await db.get_user_analytics(user_id, time_range)

        return UserAnalyticsResponse(
            user_id=user_id,
            **analytics_data
        )

    except Exception as e:
        logger.error(f"Failed to get user analytics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics: {str(e)}")

# ============= Service Analytics =============


@router.get("/analytics/service/{service_type}", response_model=ServiceAnalyticsResponse, tags=["Analytics"])
async def get_service_analytics(
    service_type: ServiceType,
    time_range: TimeRange = Query(
        TimeRange.ALL, description="Time range for analytics")
):
    """
    Get analytics for a specific service

    Available services:
    - llm_chat: LLM Chat service
    - text_to_image: Text-to-Image service
    - text_to_speech: Text-to-Speech service
    """
    try:
        analytics_data = await db.get_service_analytics(service_type, time_range)

        return ServiceAnalyticsResponse(**analytics_data)

    except Exception as e:
        logger.error(f"Failed to get service analytics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics: {str(e)}")

# ============= System Analytics =============


@router.get("/analytics/system", response_model=SystemAnalyticsResponse, tags=["Analytics"])
async def get_system_analytics(
    time_range: TimeRange = Query(
        TimeRange.ALL, description="Time range for analytics"),
    top_users_limit: int = Query(
        10, description="Number of top users to return")
):
    """
    Get system-wide analytics across all services

    Returns:
    - Total requests across all services
    - Total unique users
    - Per-service breakdown
    - Top users by request count
    """
    try:
        analytics_data = await db.get_system_analytics(time_range, top_users_limit)

        return SystemAnalyticsResponse(**analytics_data)

    except Exception as e:
        logger.error(f"Failed to get system analytics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics: {str(e)}")

# ============= Usage Statistics =============


@router.get("/analytics/usage", response_model=UsageStatsResponse, tags=["Analytics"])
async def get_usage_stats(
    user_id: Optional[str] = Query(
        None, description="User ID (leave empty for all users)"),
    time_range: TimeRange = Query(
        TimeRange.WEEK, description="Time range for statistics"),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get detailed usage statistics

    Returns:
    - Request counts by time period (hourly/daily)
    - Request counts by service
    - Success rates by service
    """
    try:
        # If no user_id and user is authenticated, use current user
        query_user_id = user_id
        if query_user_id is None and current_user:
            query_user_id = current_user.get("userId")

        stats_data = await db.get_usage_stats(query_user_id, time_range)

        return UsageStatsResponse(**stats_data)

    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}")

# ============= Root Endpoint =============


@router.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Analytics API",
        "version": "1.0.0",
        "description": "Analytics and usage tracking for LLM microservices platform",
        "endpoints": {
            "health": "GET /health",
            "track_event": "POST /analytics/track",
            "user_analytics": "GET /analytics/user",
            "my_analytics": "GET /analytics/user/me",
            "service_analytics": "GET /analytics/service/{service_type}",
            "system_analytics": "GET /analytics/system",
            "usage_stats": "GET /analytics/usage"
        },
        "services_tracked": [
            "llm_chat",
            "text_to_image",
            "text_to_speech"
        ]
    }
