import os

import pytest
from testcontainers.postgres import PostgresContainer

_pg_container: PostgresContainer | None = None


def _asyncpg_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://").replace(
        "postgresql://", "postgresql+asyncpg://"
    )


@pytest.fixture(scope="session")
def postgres_url():
    global _pg_container
    _pg_container = PostgresContainer("postgres:16-alpine")
    _pg_container.start()
    url = _asyncpg_url(_pg_container.get_connection_url())
    os.environ["DATABASE_URL"] = url
    yield url
    _pg_container.stop()


@pytest.fixture
async def db_engine(postgres_url):
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core.db import Base

    engine = create_async_engine(postgres_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
