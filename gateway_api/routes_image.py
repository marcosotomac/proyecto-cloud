from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional
import logging
import time

from models import ImageGenerationRequest, ImageGenerationResponse
from service_client import image_client
from auth import security, get_current_user, get_auth_header
from analytics import AnalyticsMiddleware

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/image", tags=["Text-to-Image"])
analytics = AnalyticsMiddleware("text_to_image")


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Generate image from text prompt

    Proxies to Text-to-Image Service and tracks analytics
    """
    start_time = time.time()
    user_id = current_user.get("userId") if current_user else None

    try:
        headers = get_auth_header(credentials)

        response = await image_client.request(
            method="POST",
            endpoint="/image/generate",
            headers=headers,
            json=request.model_dump()
        )

        response_time_ms = (time.time() - start_time) * 1000

        if response.status_code == 200:
            data = response.json()

            # Track analytics
            await analytics.track_request(
                user_id=user_id,
                success=True,
                metadata={
                    "prompt_length": len(request.prompt),
                    "image_size": f"{request.width}x{request.height}",
                    "model": request.model or "default",
                    "response_time_ms": response_time_ms
                }
            )

            return data
        else:
            # Track error
            await analytics.track_request(
                user_id=user_id,
                success=False,
                metadata={"response_time_ms": response_time_ms}
            )

            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Image generation failed")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image generation error: {str(e)}")

        # Track error
        await analytics.track_request(
            user_id=user_id,
            success=False,
            metadata={"error": str(e)}
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Text-to-Image service unavailable"
        )


@router.get("/{image_id}")
async def get_image_info(
    image_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Get information about a generated image

    Proxies to Text-to-Image Service
    """
    try:
        headers = get_auth_header(credentials)

        response = await image_client.request(
            method="GET",
            endpoint=f"/image/{image_id}",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Image not found")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get image info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Text-to-Image service unavailable"
        )


@router.get("/{image_id}/download")
async def get_image_download(
    image_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Get download URL for generated image

    Proxies to Text-to-Image Service
    """
    try:
        headers = get_auth_header(credentials)

        response = await image_client.request(
            method="GET",
            endpoint=f"/image/{image_id}/download",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Image not found")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get image download error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Text-to-Image service unavailable"
        )
