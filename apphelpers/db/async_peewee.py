import datetime
import logging
import os
from contextlib import asynccontextmanager
from functools import wraps

import pytz
from playhouse.postgres_ext import DateTimeTZField
from playhouse.pwasyncio import AsyncModel, AsyncPostgresqlDatabase
from playhouse.shortcuts import model_to_dict


def set_peewee_debug():
    logger = logging.getLogger("peewee")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)


def create_pgdb_pool(
    host=None,
    database=None,
    user=None,
    password=None,
    port=None,
    sslmode=None,
    pool_size=32,
    pool_min_size=1,
    acquire_timeout=10,
    **options,
):
    if sslmode is not None:
        if "ssl" in options:
            raise ValueError("Specify either sslmode or ssl, not both")
        options["ssl"] = sslmode

    return AsyncPostgresqlDatabase(
        database=database,
        host=host,
        user=user,
        password=password,
        port=port,
        pool_size=pool_size,
        pool_min_size=pool_min_size,
        acquire_timeout=acquire_timeout,
        **options,
    )


def create_base_model(db):
    class BaseModel(AsyncModel):
        class Meta:
            database = db
            only_save_dirty = True

        def to_dict(self, only=None, exclude=None, recurse=False, **kwargs):
            return model_to_dict(
                self,
                only=only,
                exclude=exclude,
                recurse=recurse,
                **kwargs,
            )

    return BaseModel


def created():
    return DateTimeTZField(default=lambda: datetime.datetime.now(pytz.utc))


@asynccontextmanager
async def dbtransaction_ctx(db):
    if not db.in_transaction():
        async with db:
            async with db.atomic():
                yield
    else:
        async with db.atomic():
            yield


def dbtransaction(db):
    """
    wrapper that make db transactions automic
    note db connections are used only when it is needed (hence there is no
    usual connection open/close)
    """

    def wrapper(f):
        @wraps(f)
        async def f_wrapped(*args, **kw):
            async with dbtransaction_ctx(db):
                return await f(*args, **kw)

        return f_wrapped

    return wrapper


def dbc(db):
    """
    Returns a string representing the current state of the database connection pool.
    Format: [pid]: in_use:pool_size
    """
    pid = os.getpid()
    states = getattr(getattr(db, "_state", None), "_states", {})
    in_use = sum(
        state.conn is not None and not state.closed for state in states.values()
    )
    return f"[{pid}]: {in_use}:{db._pool_size}"


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


async def setup_db(db, models):
    async with db:
        await db.acreate_tables(models, safe=True)


async def setup_db_from_basemodel(db, basemodel):
    models = get_sub_models(basemodel)
    return await setup_db(db, models)


async def destroy_db(models):
    for o in models[::-1]:
        db = o._meta.database
        async with db:
            if await db.run(o.table_exists):
                await db.adrop_tables([o])
                print("DROP: " + o._meta.name)
