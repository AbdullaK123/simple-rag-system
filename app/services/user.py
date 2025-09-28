from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import User
from typing import Optional
from app.schemas.auth import UserResponse, UserCredentials, UserCreate, Token, JWTClaims
from sqlmodel import select
from fastapi import HTTPException, status, Depends

from app.utils.auth import verify_password, hash_password, create_jwt, create_refresh_token
from app.config.logging import logger
from app.utils.errors import handle_unchecked_errors
from app.dependencies.database import get_db


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    @handle_unchecked_errors
    async def get_by_id(self, user_id: str) -> Optional[UserResponse]:
        logger.debug("Fetching user by id", extra={"user_id": user_id})
        stmt = select(User).where(User.id == user_id)
        user = (await self.db.execute(stmt)).scalar_one_or_none()
        if not user:
            logger.warning("User not found by id", extra={"user_id": user_id})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        logger.info("User fetched by id", extra={"user_id": user_id})
        return UserResponse.from_user(user)

    @handle_unchecked_errors
    async def get_by_email(self, email: str) -> Optional[UserResponse]:
        redacted_email = email if email is None else email[:3] + "***"
        logger.debug("Fetching user by email", extra={"email": redacted_email})
        stmt = select(User).where(User.email == email)
        user = (await self.db.execute(stmt)).scalar_one_or_none()
        if not user:
            logger.warning("User not found by email", extra={"email": redacted_email})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        logger.info("User fetched by email", extra={"email": redacted_email})
        return UserResponse.from_user(user)

    @handle_unchecked_errors
    async def authenticate_user(self, credentials: UserCredentials) -> User:
        redacted_email = credentials.email[:3] + "***"
        logger.debug("Authenticating user", extra={"email": redacted_email})
        stmt = select(User).where(User.email == credentials.email)
        user = (await self.db.execute(stmt)).scalar_one_or_none()
        if not user or not verify_password(user.hashed_password, credentials.password):
            logger.warning("Authentication failed", extra={"email": redacted_email})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        logger.info("Authentication successful", extra={"user_id": user.id, "email": redacted_email})
        return user

    @handle_unchecked_errors
    async def create_user(self, payload: UserCreate) -> UserResponse:
        redacted_email = payload.email[:3] + "***"
        logger.debug("Creating user", extra={"username": payload.username, "email": redacted_email})
        if user := await self.get_by_email(str(payload.email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        hashed_password = hash_password(payload.password)
        user = User(username=payload.username, email=payload.email, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        logger.info("User created", extra={"user_id": user.id, "username": user.username, "email": redacted_email})
        return UserResponse.from_user(user)

    @handle_unchecked_errors
    async def login_user(self, payload: UserCredentials) -> Token:
        user = await self.authenticate_user(payload)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        claims = JWTClaims.new(user.id)
        access_token = create_jwt(claims)
        refresh_token = create_refresh_token()
        return Token(access_token=access_token, refresh_token=refresh_token)




