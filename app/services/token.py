from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import RefreshToken, BlacklistedToken
from app.utils.errors import handle_unchecked_errors
from sqlmodel import select


class TokenService:

    def __init__(self, db: AsyncSession):
        self.db = db

    @handle_unchecked_errors
    async def get_refresh_token(self, refresh_token: str) -> RefreshToken:
        stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        token = (await self.db.execute(stmt)).first_or_none()
        return token

    @handle_unchecked_errors
    async def create_refresh_token(self, refresh_token: str):
        token = RefreshToken(token=refresh_token)
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)


