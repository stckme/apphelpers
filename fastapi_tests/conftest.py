"""
This file marks the root of tests.
Common pytest fixtures can be defines here.
See https://docs.pytest.org/en/latest/reference/fixtures.html
"""

import pytest
from httpx import ASGITransport, AsyncClient

import settings
from apphelpers.async_sessions import SessionDBHandler
from fastapi_tests import service


sessiondb_conn = dict(
    host=settings.SESSIONSDB_HOST,
    port=settings.SESSIONSDB_PORT,
    password=settings.SESSIONSDB_PASSWD,
    db=settings.SESSIONSDB_NO,
)


@pytest.fixture
async def sessionsdb():
    sessionsdb = SessionDBHandler(sessiondb_conn)
    yield sessionsdb
    await sessionsdb.close()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=service.app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
async def setup():
    from apphelpers.db.piccolo import destroy_db_from_basetable, setup_db_from_basetable
    from fastapi_tests.app.models import BaseTable

    sessionsdb = SessionDBHandler(sessiondb_conn)
    await sessionsdb.destroy_all()
    destroy_db_from_basetable(BaseTable)
    setup_db_from_basetable(BaseTable)
