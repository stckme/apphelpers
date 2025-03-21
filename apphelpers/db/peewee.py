import datetime
import logging
import os
from contextlib import contextmanager
from enum import Enum

import pytz
from peewee import Field, Model
from playhouse.pool import PooledPostgresqlExtDatabase
from playhouse.postgres_ext import DateTimeTZField
from playhouse.shortcuts import model_to_dict

try:
    from hug.decorators import wraps
except ModuleNotFoundError:
    from functools import wraps


def set_peewee_debug():
    logger = logging.getLogger("peewee")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)


class URLField(Field):
    field_type = "text"

    def python_value(self, value):
        value = value.lower()
        if not value.startswith("http") or "://" not in value:
            raise TypeError("Not a http URL: %s" % value)
        return value


def create_pgdb_pool(
    host=None,
    database=None,
    user=None,
    password=None,
    port=None,
    sslmode=None,
    max_connections=32,
):
    return PooledPostgresqlExtDatabase(
        database=database,
        host=host,
        user=user,
        password=password,
        port=port,
        sslmode=sslmode,
        max_connections=max_connections,
        register_hstore=False,
        stale_timeout=60 * 2,
    )  # 2 minutes


def create_base_model(db):
    class BaseModel(Model):
        class Meta:
            database = db
            only_save_dirty = True

        def to_dict(self, only=None, exclude=None, recurse=False):
            return model_to_dict(
                self,
                only=only,
                exclude=exclude,
                recurse=recurse,
            )

    return BaseModel


def created():
    return DateTimeTZField(default=lambda: datetime.datetime.now(pytz.utc))


@contextmanager
def dbtransaction_ctx(db):
    if not db.in_transaction():
        with db.connection_context():
            with db.atomic():
                yield
    else:
        with db.atomic():
            yield


def dbtransaction(db):
    """
    wrapper that make db transactions automic
    note db connections are used only when it is needed (hence there is no
    usual connection open/close)
    """

    def wrapper(f):
        @wraps(f)
        def f_wrapped(*args, **kw):
            with dbtransaction_ctx(db):
                return f(*args, **kw)

        return f_wrapped

    return wrapper


def enumify(TheModel, name_field="name", val_field="id"):
    """
    Converts a model rows into an enum
    Can be effective cache for mostly unchanging data.
    Limitation: No auto updates. If you update the model and you are using
    process manager like gunicorn you would need to restart to rnsure enums
    are updated

    eg.
    >>> class Week(BaseModel):
            day = CharField()
            num = IntField()

    >>> weekenum = enumify(Week, 'day', 'num')
    >>> print(weekenum.monday.num)
    """
    fields = getattr(TheModel, name_field), getattr(TheModel, val_field)
    data = list(
        (name.replace(" ", "_").lower(), v)
        for (name, v) in TheModel.select(*fields).tuples()
    )
    return Enum(TheModel.__name__, data)


def dbc(db):
    pid = os.getpid()
    return "[%s]: %s:%s" % (pid, len(db._in_use), db.max_connections)


def get_sub_models(base_model):
    models = []
    for sub_model in base_model.__subclasses__():
        models.append(sub_model)
        models.extend(get_sub_models(sub_model))
    return models


# Useful functions for test/dev setups
# NOTE: For below functions, models is list of model classes sorted by
# dependency
# Example: [Author, Publication, Post, Comment]


def setup_db(db, models):
    db.create_tables(models, safe=True)


def setup_db_from_basemodel(db, basemodel):
    models = get_sub_models(basemodel)
    db.create_tables(models, safe=True)


def destroy_db(models):
    for o in models[::-1]:
        if o.table_exists():
            o.drop_table()
            print("DROP: " + o._meta.name)
