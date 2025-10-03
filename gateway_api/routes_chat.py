from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional
import logging
import time

from models import ChatRequest, ChatResponse
from service_client import llm_client
from auth import security, get_current_user, get_auth_header
from analytics import AnalyticsMiddleware

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["LLM Chat"])
analytics = AnalyticsMiddleware("llm_chat")


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Send chat message to LLM

    Proxies to LLM Chat Service and tracks analytics
    Auto-creates session if none provided
    """
    start_time = time.time()
    user_id = current_user.get("userId") if current_user else None

    try:
        headers = get_auth_header(credentials)
        session_id = request.session_id

        # Create session if not provided
        if not session_id:
            session_response = await llm_client.request(
                method="POST",
                endpoint="/chat/session",
                headers=headers,
                json={"model": request.model}
            )

            if session_response.status_code != 200:
                raise HTTPException(
                    status_code=session_response.status_code,
                    detail="Failed to create chat session"
                )

            session_data = session_response.json()
            session_id = session_data.get("sessionId")

        # Send message
        message_response = await llm_client.request(
            method="POST",
            endpoint="/chat/message",
            headers=headers,
            json={
                "sessionId": session_id,
                "content": request.message,
                "model": request.model
            }
        )

        response_time_ms = (time.time() - start_time) * 1000

        if message_response.status_code == 200:
            data = message_response.json()

            # Track analytics
            await analytics.track_request(
                user_id=user_id,
                success=True,
                metadata={
                    "model": data.get("model"),
                    "input_tokens": data.get("tokens", {}).get("input", 0),
                    "output_tokens": data.get("tokens", {}).get("output", 0),
                    "total_tokens": data.get("tokens", {}).get("total", 0),
                    "response_time_ms": response_time_ms
                }
            )

            # Format response to match gateway model
            return ChatResponse(
                session_id=data.get("sessionId"),
                message_id=data.get("messageId"),
                content=data.get("content"),
                role=data.get("role"),
                model=data.get("model"),
                tokens=data.get("tokens", {})
            )
        else:
            # Track error
            await analytics.track_request(
                user_id=user_id,
                success=False,
                metadata={"response_time_ms": response_time_ms}
            )

            raise HTTPException(
                status_code=message_response.status_code,
                detail=message_response.json().get("detail", "Chat request failed")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")

        # Track error
        await analytics.track_request(
            user_id=user_id,
            success=False,
            metadata={"error": str(e)}
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM Chat service unavailable"
        )


@router.get("/sessions")
async def get_sessions(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get user's chat sessions

    Proxies to LLM Chat Service
    """
    try:
        headers = get_auth_header(credentials)

        response = await llm_client.request(
            method="GET",
            endpoint="/chat/sessions",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Failed to get sessions")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM Chat service unavailable"
        )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get specific chat session

    Proxies to LLM Chat Service
    """
    try:
        headers = get_auth_header(credentials)

        response = await llm_client.request(
            method="GET",
            endpoint=f"/chat/session/{session_id}",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Failed to get session")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM Chat service unavailable"
        )


@router.get("/models")
async def get_models(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get available LLM models

    Proxies to LLM Chat Service (requires authentication)
    """
    try:
        headers = get_auth_header(credentials)

        response = await llm_client.request(
            method="GET",
            endpoint="/chat/models",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to get models"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get models error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM Chat service unavailable"
        )
