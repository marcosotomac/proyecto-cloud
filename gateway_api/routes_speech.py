from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional
import logging
import time

from models import SpeechGenerationRequest, SpeechGenerationResponse
from service_client import speech_client
from auth import security, get_current_user, get_auth_header
from analytics import AnalyticsMiddleware

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/speech", tags=["Text-to-Speech"])
analytics = AnalyticsMiddleware("text_to_speech")


@router.post("/generate", response_model=SpeechGenerationResponse)
async def generate_speech(
    request: SpeechGenerationRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Generate speech from text

    Proxies to Text-to-Speech Service and tracks analytics
    """
    start_time = time.time()
    user_id = current_user.get("userId") if current_user else None

    try:
        headers = get_auth_header(credentials)

        response = await speech_client.request(
            method="POST",
            endpoint="/tts/generate",
            headers=headers,
            json=request.model_dump()
        )

        response_time_ms = (time.time() - start_time) * 1000

        if response.status_code in [200, 201]:
            data = response.json()

            # Track analytics
            await analytics.track_request(
                user_id=user_id,
                success=True,
                metadata={
                    "text_length": len(request.prompt),
                    "voice": request.voice,
                    "language": request.language,
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
                detail=response.json().get("detail", "Speech generation failed")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speech generation error: {str(e)}")

        # Track error
        await analytics.track_request(
            user_id=user_id,
            success=False,
            metadata={"error": str(e)}
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Text-to-Speech service unavailable"
        )


@router.get("/{request_id}")
async def get_speech_info(
    request_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Get information about a generated speech

    Proxies to Text-to-Speech Service
    """
    try:
        headers = get_auth_header(credentials)

        response = await speech_client.request(
            method="GET",
            endpoint=f"/tts/{request_id}",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Speech not found")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get speech info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Text-to-Speech service unavailable"
        )


@router.get("/{request_id}/download")
async def get_speech_download(
    request_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Get download URL for generated speech

    Proxies to Text-to-Speech Service
    """
    try:
        headers = get_auth_header(credentials)

        response = await speech_client.request(
            method="GET",
            endpoint=f"/tts/{request_id}/download",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Speech not found")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get speech download error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Text-to-Speech service unavailable"
        )
