from uuid import uuid4

import pytest
from peewee import TextField

from converge import settings
from apphelpers.db.async_peewee import (
    create_base_model,
    create_pgdb_pool,
    dbtransaction,
    destroy_db,
    setup_db_from_basemodel,
)

db = create_pgdb_pool(
    host=settings.DB_HOST,
    database=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASS,
)
BaseModel = create_base_model(db)


class Book(BaseModel):
    name = TextField()

    class Meta:
        table_name = "test_async_peewee_" + uuid4().hex


async def _add_book(name):
    await Book.acreate(name=name)


async def _add_book_loser(name):
    await _add_book(name)
    raise NameError("intentional transaction rollback")


add_book = dbtransaction(db)(_add_book)
add_book_loser = dbtransaction(db)(_add_book_loser)


@pytest.fixture
async def book_table(anyio_backend):
    try:
        await setup_db_from_basemodel(db, BaseModel)
        try:
            yield
        finally:
            await destroy_db([Book])
    finally:
        await db.close_pool()


@pytest.mark.anyio
async def test_async_peewee_transactions(book_table):
    name = "The Pillars of the Earth"
    await add_book(name)
    names = [book.name for book in await Book.select().aexecute()]
    assert name in names

    name = "The Cathedral and the Bazaar"
    with pytest.raises(NameError, match="intentional transaction rollback"):
        await add_book_loser(name)
    names = [book.name for book in await Book.select().aexecute()]
    assert name not in names

    name = "The Ego Trick"
    await add_book(name)
    names = [book.name for book in await Book.select().aexecute()]
    assert name in names


def test_create_pgdb_pool_maps_asyncpg_options():
    db = create_pgdb_pool(database="test", max_connections=5, sslmode="require")

    assert db._pool_size == 5
    assert db.connect_params["ssl"] == "require"
    assert "max_connections" not in db.connect_params
    assert "sslmode" not in db.connect_params
