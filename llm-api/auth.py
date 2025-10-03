from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Optional[str]:
    """
    Extract user_id from JWT token
    Returns None if no token or invalid token (for optional authentication)
    Raises HTTPException if token is present but invalid (for required authentication)
    """
    # Try to get credentials from security scheme
    if credentials is None:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
    else:
        token = credentials.credentials

    try:
        # Decode JWT with HS256
        payload = jwt.decode(
            token,
            settings.JWT_ACCESS_SECRET,
            algorithms=["HS256"]
        )

        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing 'sub' claim")
            return None

        return str(user_id)

    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception as e:
        logger.error(f"Unexpected auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


async def require_auth(request: Request) -> str:
    """
    Require authentication - raises 401 if no valid token
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    user_id = await get_current_user(request)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return user_id
