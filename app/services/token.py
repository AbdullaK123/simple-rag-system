from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import RefreshToken, BlacklistedToken
from app.schemas.auth import Token, JWTClaims
from app.utils.auth import create_jwt, create_refresh_token
from app.utils.errors import handle_unchecked_errors
from sqlmodel import select, func, delete
from app.config.logging import logger
from typing import Optional
from fastapi import HTTPException, status


class TokenService:

    def __init__(self, db: AsyncSession):
        self.db = db

    @handle_unchecked_errors
    async def get_refresh_token(self, refresh_token: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        token = (await self.db.execute(stmt)).first_or_none()
        return token

    @handle_unchecked_errors
    async def create_refresh_token(self, refresh_token: str):
        token = RefreshToken(token=refresh_token)
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)

    @handle_unchecked_errors
    async def delete_refresh_token(self, refresh_token: str):
        stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        token = (await self.db.execute(stmt)).first_or_none()
        if token:
            self.db.delete(token)
            await self.db.commit()

    @handle_unchecked_errors
    async def blacklist_token(self, access_token: str, user_id: str):
        stmt = (
            select(BlacklistedToken)
            .where(BlacklistedToken.access_token == access_token)
        )
        if token := (await self.db.execute(stmt)).first_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Token is already blacklisted"
            )
        else:
            token = BlacklistedToken(access_token=access_token, user_id=user_id)
            self.db.add(token)
            await self.db.commit()

    @handle_unchecked_errors
    async def is_token_blacklisted(self, access_token: str) -> bool:
        stmt = select(BlacklistedToken).where(BlacklistedToken.token == access_token)
        token = (await self.db.execute(stmt)).scalar_one_or_none()
        return token is not None

    @handle_unchecked_errors
    async def refresh_token(self, refresh_token: str) -> Token:
        # Validate refresh token exists
        stored_token = await self.get_refresh_token(refresh_token)
        if not stored_token:
            raise HTTPException(401, "Invalid refresh token")

        # Create new access token
        claims = JWTClaims.new(stored_token.user_id)
        new_access_token = create_jwt(claims)
        new_refresh_token = create_refresh_token()

        # Replace old refresh token
        await self.delete_refresh_token(refresh_token)
        await self.create_refresh_token(new_refresh_token)

        return Token(access_token=new_access_token, refresh_token=new_refresh_token)

    @handle_unchecked_errors
    async def revoke_all_tokens(self) -> int:
        try:
            # Count tokens before deletion for logging
            count_stmt = select(func.count(RefreshToken.token))
            token_count = (await self.db.execute(count_stmt)).scalar()

            # Bulk delete
            await self.db.execute(delete(RefreshToken))
            await self.db.commit()

            logger.warning("Revoked all refresh tokens", extra={"count": token_count})
            return token_count
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to revoke all tokens", extra={"error": str(e)})
            raise e
