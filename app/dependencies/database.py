from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from app.dependencies.config import get_settings

app_config = get_settings()

engine = create_async_engine(
    app_config.environment.db_url,
    debug=True,
    pool_size=5,
    max_overflow=10
)

async def get_db():
    async with AsyncSession(engine, expire_on_commit=False) as db:
        yield db

