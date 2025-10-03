from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional
import logging

from models import (
    UserRegisterRequest,
    UserLoginRequest,
    UserAuthResponse
)
from service_client import users_client
from auth import security, get_auth_header

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest):
    """
    Register a new user

    Proxies to Users Service
    """
    try:
        response = await users_client.request(
            method="POST",
            endpoint="/auth/register",
            json=request.model_dump()
        )

        if response.status_code == 201:
            return response.json()
        elif response.status_code == 409:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("message", "Registration failed")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Users service unavailable"
        )


@router.post("/login")
async def login(request: UserLoginRequest):
    """
    Login user

    Proxies to Users Service
    """
    try:
        response = await users_client.request(
            method="POST",
            endpoint="/auth/login",
            json=request.model_dump()
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("message", "Login failed")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Users service unavailable"
        )


@router.post("/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Refresh access token using refresh token in Authorization header

    Proxies to Users Service
    """
    try:
        # Extract token from Authorization header
        refresh_token = credentials.credentials

        response = await users_client.request(
            method="POST",
            endpoint="/auth/refresh",
            json={"refreshToken": refresh_token}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("message", "Token refresh failed")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Users service unavailable"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout user

    Proxies to Users Service
    """
    try:
        headers = get_auth_header(credentials)

        response = await users_client.request(
            method="POST",
            endpoint="/auth/logout",
            headers=headers
        )

        if response.status_code in [200, 204]:
            return {"message": "Logged out successfully"}
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("message", "Logout failed")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Users service unavailable"
        )


@router.get("/profile")
async def get_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get user profile

    Proxies to Users Service
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        headers = get_auth_header(credentials)

        response = await users_client.request(
            method="GET",
            endpoint="/users/me",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("message", "Failed to get profile")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Users service unavailable"
        )
