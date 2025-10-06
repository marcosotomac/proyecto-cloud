"""TTS API routes"""
import time
import uuid
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from models.tts import (
    TTSGenerateRequest,
    TTSGenerateResponse,
    TTSInfoResponse,
    TTSDownloadResponse,
    TTSListResponse,
    S3Keys,
    TTSMetadata,
    ErrorResponse
)
from models.db_models import TTSConversion
from clients.pollinations import PollinationsTTSClient
from clients.s3 import s3_client
from middleware.auth import optional_auth, require_auth
from db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])

# Initialize TTS client
tts_client = PollinationsTTSClient()


@router.post(
    "/generate",
    response_model=TTSGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Generation failed"}
    }
)
async def generate_speech(
    request: TTSGenerateRequest,
    user: Optional[Dict[str, Any]] = Depends(optional_auth),
    db: Session = Depends(get_db)
):
    """
    Generate speech from text

    - Supports both authenticated and anonymous users
    - Authenticated requests are linked to user account
    - Stores audio and metadata in S3 and PostgreSQL
    - Returns S3 paths and metadata
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    user_id = user.get("user_id") if user else "anonymous"
    username = user.get("email") if user else None

    logger.info(
        f"TTS generation started: id={request_id}, user={username or 'anonymous'}")

    try:
        # Validate language code for gTTS
        # Common gTTS languages: en, es, fr, de, it, pt, ja, zh-CN, ko, ar, hi, ru, etc.
        # No strict validation - gTTS will handle invalid languages

        # Generate audio via gTTS
        audio_bytes = await tts_client.generate_speech(
            prompt=request.prompt,
            model=request.model,
            voice=request.voice
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Save to S3
        s3_keys = s3_client.save_tts_history(
            request_id=request_id,
            user_id=user_id,
            username=username,
            prompt=request.prompt,
            audio_bytes=audio_bytes,
            model=request.model,
            voice=request.voice,
            provider="gtts",
            latency_ms=latency_ms,
            status_code=200,
            cost_usd=0.0,  # gTTS is free
            meta={
                "audio_size_bytes": len(audio_bytes),
                "voice": request.voice
            }
        )

        # Save to PostgreSQL database
        try:
            from config import settings
            db_conversion = TTSConversion(
                user_id=str(user_id),
                text=request.prompt,
                audio_url=s3_keys["audio"],
                model=request.model or "gtts",
                voice=request.voice or "default",
                language=request.voice or "en",  # gTTS uses voice param as language
                file_size_bytes=len(audio_bytes),
                s3_key=s3_keys["audio"],
                s3_bucket=settings.s3_bucket,
                extra_metadata={
                    "request_id": request_id,
                    "provider": "gtts",
                    "latency_ms": latency_ms,
                    "status_code": 200,
                    "cost_usd": 0.0,
                    "record_key": s3_keys["record"],
                    "input_key": s3_keys.get("input")
                }
            )
            db.add(db_conversion)
            db.commit()
            db.refresh(db_conversion)
            logger.info(
                f"TTS conversion saved to database: db_id={db_conversion.id}")
        except Exception as db_error:
            logger.error(
                f"Failed to save to database: {db_error}", exc_info=True)
            # Don't fail the request if DB save fails
            db.rollback()

        logger.info(
            f"TTS generation completed: id={request_id}, latency={latency_ms}ms")

        return TTSGenerateResponse(
            id=request_id,
            s3=S3Keys(
                record=s3_keys["record"],
                audio=s3_keys["audio"],
                input=s3_keys.get("input")
            ),
            meta=TTSMetadata(
                provider="gtts",
                model=request.model,
                voice=request.voice,
                processing_time_ms=latency_ms
            ),
            created_at=datetime.utcnow(),
            user_id=user_id,
            status="completed"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS generation failed: {str(e)}"
        )


@router.get(
    "/{request_id}",
    response_model=TTSInfoResponse,
    responses={
        404: {"model": ErrorResponse, "description": "TTS request not found"}
    }
)
async def get_tts_info(request_id: str):
    """
    Get information about a TTS generation

    Note: Requires approximate date for efficient S3 lookup
    For now, tries recent dates
    """
    # Try to find the record in recent dates
    now = datetime.utcnow()

    for days_ago in range(7):  # Search last 7 days
        date = datetime(now.year, now.month, now.day) - \
            timedelta(days=days_ago)
        record = s3_client.get_record(request_id, date)

        if record:
            return TTSInfoResponse(
                id=record["id"],
                prompt=record["prompt"][:100] +
                "..." if len(record["prompt"]) > 100 else record["prompt"],
                model=record["model"],
                voice=record["voice"],
                status="completed",
                created_at=datetime.fromisoformat(
                    record["createdAt"].rstrip("Z")),
                user_id=record.get("userId"),
                s3_key=record["artifacts"]["audio"]
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"TTS request {request_id} not found"
    )


@router.get(
    "/{request_id}/download",
    response_model=TTSDownloadResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Audio not found"}
    }
)
async def get_download_url(request_id: str):
    """
    Get a signed URL for downloading the audio file

    - URL expires in 5 minutes
    - Works for both authenticated and anonymous users
    """
    # Find the record
    now = datetime.utcnow()

    for days_ago in range(7):
        date = datetime(now.year, now.month, now.day) - \
            timedelta(days=days_ago)
        record = s3_client.get_record(request_id, date)

        if record:
            audio_key = record["artifacts"]["audio"]
            signed_url = s3_client.get_signed_url(audio_key, expires_in=300)

            return TTSDownloadResponse(
                download_url=signed_url,
                expires_in=300
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Audio for request {request_id} not found"
    )


@router.get(
    "/admin/audios",
    response_model=TTSListResponse,
    dependencies=[Depends(require_auth)]
)
async def list_user_audios(
    user: Dict[str, Any] = Depends(require_auth),
    page: int = 1,
    per_page: int = 10
):
    """
    List user's TTS generations (requires authentication)

    - Returns paginated list
    - Only accessible to authenticated users
    """
    user_id = user["user_id"]

    # Get user's audio history
    audio_keys = s3_client.list_user_audios(user_id, limit=per_page)

    # For now, return simplified response
    # In production, parse the JSONL history files

    return TTSListResponse(
        audios=[],
        total=len(audio_keys),
        page=page,
        per_page=per_page
    )
