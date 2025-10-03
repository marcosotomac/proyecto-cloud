from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional
import logging

from service_client import analytics_client
from auth import security, require_auth, get_auth_header, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/user/me")
async def get_my_analytics(
    time_range: str = Query(
        "all", description="Time range: hour, day, week, month, year, all"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    current_user: dict = Depends(require_auth)
):
    """
    Get analytics for current authenticated user

    Proxies to Analytics Service
    """
    try:
        headers = get_auth_header(credentials)

        response = await analytics_client.request(
            method="GET",
            endpoint="/analytics/user/me",
            headers=headers,
            params={"time_range": time_range}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Failed to get analytics")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get analytics error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Analytics service unavailable"
        )


@router.get("/service/{service_type}")
async def get_service_analytics(
    service_type: str,
    time_range: str = Query(
        "all", description="Time range: hour, day, week, month, year, all")
):
    """
    Get analytics for a specific service

    Available services: llm_chat, text_to_image, text_to_speech

    Proxies to Analytics Service
    """
    try:
        response = await analytics_client.request(
            method="GET",
            endpoint=f"/analytics/service/{service_type}",
            params={"time_range": time_range}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Failed to get service analytics")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get service analytics error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Analytics service unavailable"
        )


@router.get("/system")
async def get_system_analytics(
    time_range: str = Query(
        "all", description="Time range: hour, day, week, month, year, all"),
    top_users_limit: int = Query(
        10, description="Number of top users to return")
):
    """
    Get system-wide analytics

    Proxies to Analytics Service
    """
    try:
        response = await analytics_client.request(
            method="GET",
            endpoint="/analytics/system",
            params={
                "time_range": time_range,
                "top_users_limit": top_users_limit
            }
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Failed to get system analytics")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get system analytics error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Analytics service unavailable"
        )


@router.get("/usage")
async def get_usage_stats(
    time_range: str = Query(
        "week", description="Time range: hour, day, week, month, year, all"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get detailed usage statistics

    Proxies to Analytics Service
    """
    try:
        headers = get_auth_header(credentials)

        response = await analytics_client.request(
            method="GET",
            endpoint="/analytics/usage",
            headers=headers,
            params={"time_range": time_range}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Failed to get usage stats")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get usage stats error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Analytics service unavailable"
        )
