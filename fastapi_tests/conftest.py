"""
This file marks the root of tests.
Common pytest fixtures can be defines here.
See https://docs.pytest.org/en/latest/reference/fixtures.html
"""

import asyncio
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


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def sessionsdb():
    sessionsdb = SessionDBHandler(sessiondb_conn)
    yield sessionsdb
    await sessionsdb.close()


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=service.app), base_url="http://test"
    ) as ac:
        yield ac
