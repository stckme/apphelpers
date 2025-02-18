import asyncio

from piccolo import columns as col
from piccolo.engine.postgres import PostgresEngine
import pytest

import settings
from apphelpers.db.piccolo import (
    BaseTable,
    dbtransaction,
    destroy_db_from_basetable,
    setup_db_from_basetable,
)

db = PostgresEngine(
    config=dict(
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASS,
    )
)
dbtransaction_wrapper = dbtransaction(db)


class Book(BaseTable, db=db):
    name = col.Text()


async def _add_book(name):
    await Book.insert(Book(name=name)).run()


async def _add_book_loser(name):
    await _add_book(name)
    loser  # will raise  # noqa: F821


def setup_module():
    setup_db_from_basetable(BaseTable)


def teardown_module():
    destroy_db_from_basetable(BaseTable)


async def add_with_tr():
    add_book = dbtransaction_wrapper(_add_book)
    name = "The Pillars of the Earth"
    await add_book(name)
    names = [b[Book.name] for b in await Book.select().run()]
    assert name in names

    add_book_loser = dbtransaction_wrapper(_add_book_loser)
    name = "The Cathedral and the Bazaar"
    with pytest.raises(NameError):
        await add_book_loser(name)
    names = [b[Book.name] for b in await Book.select().run()]
    assert name not in names

    add_book = dbtransaction_wrapper(_add_book)
    name = "The Ego Trick"
    await add_book(name)
    names = [b[Book.name] for b in await Book.select().run()]
    assert name in names


def test_add_with_tr():
    asyncio.run(add_with_tr())
