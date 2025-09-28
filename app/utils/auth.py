import jwt
from passlib.context import CryptContext
from app.dependencies.config import get_settings
from app.schemas.auth import JWTClaims
import secrets
from app.config.logging import logger

settings = get_settings()

context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    logger.debug("Hashing password")
    return context.hash(password)

def verify_password(hashed_password: str, password: str) -> bool:
    logger.debug("Verifying password")
    return context.verify(password, hashed_password)

def create_jwt(data: JWTClaims) -> str:
    logger.debug("Creating JWT", extra={"sub": getattr(data, 'sub', None)})
    return jwt.encode(
        data.to_jwt_payload(),
        key=settings.auth.jwt_secret_key.get_secret_value(),
        algorithm=settings.auth.jwt_algorithm
    )

def decode_jwt(token: str) -> JWTClaims:
    logger.debug("Decoding JWT", extra={"token_prefix": token[:8] + "...", "alg": settings.auth.jwt_algorithm})
    decoded_data = jwt.decode(
        token,
        key=settings.auth.jwt_secret_key.get_secret_value(),
        algorithms=[settings.auth.jwt_algorithm]
    )
    logger.debug("Decoded JWT claims", extra={"keys": list(decoded_data.keys())})
    return JWTClaims(**decoded_data)

def create_refresh_token() -> str:
    token = secrets.token_urlsafe(32)
    logger.debug("Generated refresh token", extra={"length": len(token)})
    return token