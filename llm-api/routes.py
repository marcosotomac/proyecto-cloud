from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from models import (
    CreateSessionRequest, CreateSessionResponse,
    SendMessageRequest, SendMessageResponse,
    GetSessionResponse, GetSessionHistoryResponse,
    MessageHistoryItem, TokenCount
)
from db import mongo_client
from github_models import github_client
from auth import require_auth
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/session", response_model=CreateSessionResponse)
async def create_chat_session(
    request: Request,
    body: CreateSessionRequest
):
    """
    Create a new chat session
    Requires authentication
    """
    user_id = await require_auth(request)

    # Use default model if not specified
    model = body.model or settings.GITHUB_DEFAULT_MODEL

    # Create session in MongoDB
    session_id = await mongo_client.create_session(
        user_id=user_id,
        title=body.title,
        model=model
    )

    logger.info(f"Created session {session_id} for user {user_id}")

    from datetime import datetime
    return CreateSessionResponse(
        sessionId=session_id,
        title=body.title,
        model=model,
        createdAt=datetime.utcnow()
    )


@router.post("/message", response_model=SendMessageResponse)
async def send_chat_message(
    request: Request,
    body: SendMessageRequest
):
    """
    Send a message to a chat session and get LLM response
    Requires authentication
    """
    user_id = await require_auth(request)

    # Verify session exists and belongs to user
    session = await mongo_client.get_session(body.sessionId, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )

    # Use session model or override
    model = body.model or session["model"]

    try:
        # Get conversation history
        history = await mongo_client.get_session_messages(body.sessionId)

        # Build messages for GitHub Models (include history)
        messages = []
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add new user message
        messages.append({
            "role": "user",
            "content": body.content
        })

        # Save user message to DB
        user_message_id = await mongo_client.create_message(
            session_id=body.sessionId,
            user_id=user_id,
            role="user",
            content=body.content,
            model=model,
            tokens_in=0,  # Will be updated with actual count
            tokens_out=0
        )

        # Call GitHub Models for completion
        response = await github_client.chat(messages=messages, model=model)

        assistant_content = response["content"]
        tokens_in = response["tokens_in"]
        tokens_out = response["tokens_out"]

        # Save assistant message to DB
        assistant_message_id = await mongo_client.create_message(
            session_id=body.sessionId,
            user_id=user_id,
            role="assistant",
            content=assistant_content,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out
        )

        # Update session counters
        await mongo_client.update_session_counters(
            session_id=body.sessionId,
            user_id=user_id,
            increment_messages=2,  # user + assistant
            increment_tokens_in=tokens_in,
            increment_tokens_out=tokens_out
        )

        logger.info(
            f"Message sent to session {body.sessionId}: {tokens_in} in, {tokens_out} out")

        from datetime import datetime
        return SendMessageResponse(
            messageId=assistant_message_id,
            sessionId=body.sessionId,
            role="assistant",
            content=assistant_content,
            model=model,
            tokens=TokenCount(input=tokens_in, output=tokens_out),
            createdAt=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=GetSessionHistoryResponse)
async def get_chat_session_history(
    request: Request,
    session_id: str
):
    """
    Get chat session with full message history
    Requires authentication
    """
    user_id = await require_auth(request)

    # Get session
    session = await mongo_client.get_session(session_id, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )

    # Get messages
    messages = await mongo_client.get_session_messages(session_id)

    # Format response
    session_response = GetSessionResponse(
        sessionId=str(session["_id"]),
        title=session["title"],
        model=session["model"],
        counters=session["counters"],
        lastMessageAt=session.get("lastMessageAt"),
        createdAt=session["createdAt"],
        updatedAt=session["updatedAt"]
    )

    message_items = [
        MessageHistoryItem(
            messageId=str(msg["_id"]),
            role=msg["role"],
            content=msg["content"],
            tokens=TokenCount(
                input=msg["tokens"]["input"],
                output=msg["tokens"]["output"]
            ),
            createdAt=msg["createdAt"]
        )
        for msg in messages
    ]

    return GetSessionHistoryResponse(
        session=session_response,
        messages=message_items
    )


@router.get("/sessions", response_model=List[GetSessionResponse])
async def list_chat_sessions(
    request: Request,
    limit: int = 20,
    skip: int = 0
):
    """
    List user's chat sessions
    Requires authentication
    """
    user_id = await require_auth(request)

    sessions = await mongo_client.list_user_sessions(
        user_id=user_id,
        limit=limit,
        skip=skip
    )

    return [
        GetSessionResponse(
            sessionId=str(session["_id"]),
            title=session["title"],
            model=session["model"],
            counters=session["counters"],
            lastMessageAt=session.get("lastMessageAt"),
            createdAt=session["createdAt"],
            updatedAt=session["updatedAt"]
        )
        for session in sessions
    ]


@router.get("/models")
async def list_available_models(request: Request):
    """
    List available GitHub Models
    Requires authentication
    """
    await require_auth(request)

    models = await github_client.list_models()
    return {"models": models}
