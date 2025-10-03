"""Authentication middleware for Text-to-Speech API"""
import httpx
import jwt
import logging
from fastapi import Request, HTTPException, status
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """JWT authentication middleware"""

    def __init__(self):
        self.users_service_url = settings.users_service_url + "/users/me"  # Fixed endpoint
        self.jwt_secret = settings.jwt_access_secret
        self.jwt_public_key = self._load_public_key()

    def _load_public_key(self) -> Optional[str]:
        """Load JWT public key from file (for RS256, not used currently)"""
        try:
            with open(settings.jwt_public_key_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(
                f"JWT public key not found at {settings.jwt_public_key_path}")
            return None
        except Exception as e:
            logger.error(f"Error loading JWT public key: {e}")
            return None

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token locally using HS256 secret

        Returns:
            User data from token
        """
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authorization token provided"
            )

        # Verify token with HS256 (symmetric key)
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"]
            )
            logger.info(
                f"Token verified locally for user: {payload.get('sub')}")
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role", "user")
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    async def get_user_from_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Extract and verify user from request

        Returns:
            User data or None if not authenticated
        """
        auth_header = request.headers.get("Authorization", "")

        logger.info(
            f"Auth header received: {auth_header[:50] if auth_header else 'None'}...")

        if not auth_header.startswith("Bearer "):
            logger.info("No Bearer token in Authorization header")
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix
        logger.info(f"Extracted token (first 20 chars): {token[:20]}...")

        try:
            user_data = await self.verify_token(token)
            logger.info(f"User authenticated: {user_data}")
            return user_data
        except HTTPException as e:
            logger.warning(f"Authentication failed: {e.detail}")
            return None
        except Exception as e:
            logger.error(f"Unexpected auth error: {e}")
            return None


# Global instance
auth_middleware = AuthMiddleware()


async def require_auth(request: Request) -> Dict[str, Any]:
    """
    Dependency that requires authentication

    Usage in FastAPI:
        @app.get("/protected", dependencies=[Depends(require_auth)])
    """
    user = await auth_middleware.get_user_from_request(request)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    return user


async def optional_auth(request: Request) -> Optional[Dict[str, Any]]:
    """
    Dependency for optional authentication

    Returns user data if authenticated, None otherwise
    """
    return await auth_middleware.get_user_from_request(request)
