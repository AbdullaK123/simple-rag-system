from app.dependencies.services import get_user_service
from app.schemas.auth import UserResponse
from app.services.user import UserService
from app.utils.auth import decode_jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
import jwt
from app.config.logging import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    service: UserService = Depends(get_user_service),
    token: str = Depends(oauth2_scheme)
) -> UserResponse:
    logger.debug("Resolving current user from token", extra={"token_prefix": token[:8] + "..." if token else None})
    try:
        payload = decode_jwt(token)
        sub = payload['sub'] if isinstance(payload, dict) else getattr(payload, 'sub', None)
        user = await service.get_by_id(sub)
        if not user:
            logger.warning("Token resolved to unknown user", extra={"sub": sub})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        logger.info("Resolved current user", extra={"user_id": user.id})
        return UserResponse.from_user(user)
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")