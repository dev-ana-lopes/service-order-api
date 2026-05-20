from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..config.settings import Settings


class DatabaseSession:
    def __init__(self, settings: Settings):
        self.async_engine = create_async_engine(
            settings.database_url_async,
            echo=False,
            pool_size=10,
            max_overflow=20,
        )
        self.async_session_maker = sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncSession:
        async with self.async_session_maker() as session:
            yield session

    async def ping(self) -> bool:
        try:
            async with self.async_engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def dispose(self) -> None:
        await self.async_engine.dispose()
