from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "dev",
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy.

    Alembic usa Base.metadata para la autogeneración de migraciones.
    Todos los modelos deben importarse en alembic/env.py para que sean detectados.
    """


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency de FastAPI para obtener una sesión de base de datos."""
    async with AsyncSessionLocal() as session:
        yield session
