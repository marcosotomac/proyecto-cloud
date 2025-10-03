from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional, Dict, Any
import httpx
import logging
from app.config import settings

security = HTTPBearer()
logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.users_service_url = getattr(
            settings, 'users_service_url', 'http://users-service:3000')
        self.jwt_secret = settings.jwt_access_secret

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica el token JWT localmente usando HS256

        Returns:
            User data from token
        """
        try:
            # Verificar token con HS256 (clave simétrica)
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
            logger.warning("Token has expired")
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
        except Exception as e:
            logger.error(f"Unexpected auth error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )


auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency para obtener el usuario actual autenticado"""
    token = credentials.credentials
    return await auth_service.verify_token(token)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """Dependency opcional para obtener el usuario (permite anonimos)"""
    if credentials is None:
        logger.info("No credentials provided, returning None (anonymous)")
        return None

    try:
        token = credentials.credentials
        logger.info(
            f"Verifying optional token (first 20 chars): {token[:20]}...")
        user_data = await auth_service.verify_token(token)
        logger.info(f"Optional auth successful: {user_data}")
        return user_data
    except HTTPException as e:
        logger.warning(f"Optional auth failed: {e.detail}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in optional auth: {e}")
        return None
