import os
import datetime
from functools import wraps
from enum import Enum

from peewee import DateTimeField, Model
from playhouse.pool import PooledPostgresqlExtDatabase
from playhouse.shortcuts import model_to_dict


def create_pgdb_pool(
    host=None, database=None, user=None, password=None, max_connections=32
):
    return PooledPostgresqlExtDatabase(
        database=database,
        host=host,
        user=user,
        password=password,
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
            return model_to_dict(self, only=only, exclude=exclude, recurse=recurse)

    return BaseModel


created = lambda: DateTimeField(default=datetime.datetime.utcnow)


def dbtransaction(db, f):
    """
    wrapper that make db transactions automic
    note db connections are used only when it is needed (hence there is no usual connection open/close)
    """

    @wraps(f)
    def wrapper(*args, **kw):
        if not db.in_transaction():
            with db.connection_context():
                with db.atomic():
                    result = f(*args, **kw)
        else:
            with db.atomic():
                result = f(*args, **kw)
        return result

    return wrapper


def enumify(TheModel, name_field="name", val_field="id"):
    """
    Converts a model rows into an enum
    Can be effective cache for mostly unchanging data.
    Limitation: No auto updates. If you update the model and you are using process manager like gunicorn you
    would need to restart to rnsure enums are updated

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
