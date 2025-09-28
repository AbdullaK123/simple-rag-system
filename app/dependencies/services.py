from app.dependencies.database import get_db
from app.services.user import UserService
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends


def get_user_service(
    db: AsyncSession = Depends(get_db)
) -> 'UserService':
    return UserService(db)