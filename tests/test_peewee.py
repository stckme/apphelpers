from apphelpers.db.peewee import create_pgdb_pool, create_base_model, dbtransaction
from peewee import TextField

import settings

db = create_pgdb_pool(database=settings.DB_NAME, user=settings.DB_USER)
BaseModel = create_base_model(db)
dbtransaction = dbtransaction(db)


class Book(BaseModel):
    name = TextField()


def _add_book(name):
    Book.create(name=name)


def _add_book_loser(name):
    _add_book(name)
    loser  # will raise


def setup_module():
    Book.create_table()


def teardown_module():
    Book.drop_table()


def test_add_with_tr():
    add_book = dbtransaction(_add_book)
    name = "The Pillars of the Earth"
    add_book(name)
    names = [b.name for b in Book.select()]
    assert name in names

    add_book_loser = dbtransaction(_add_book_loser)
    name = "The Cathedral and the Bazaar"
    try:
        add_book_loser(name)
    except NameError:
        pass
    names = [b.name for b in Book.select()]
    assert name not in names

    add_book = dbtransaction(_add_book)
    name = "The Ego Trick"
    add_book(name)
    names = [b.name for b in Book.select()]
    assert name in names
