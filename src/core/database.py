"""Engine y sesión async de SQLAlchemy.

- En local usa SQLite (aiosqlite).
- En Railway/producción usa PostgreSQL (asyncpg) vía DATABASE_URL.

`get_session` es la dependencia de FastAPI que inyecta una AsyncSession por
request y la cierra al terminar.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa de la que heredan todos los modelos."""


engine = create_async_engine(
    settings.sqlalchemy_url,
    echo=False,
    future=True,
    pool_pre_ping=not settings.is_sqlite,
    connect_args=settings.db_connect_args,
)

SessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
