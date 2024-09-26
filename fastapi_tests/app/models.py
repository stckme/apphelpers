from piccolo import columns as col
from piccolo.engine.postgres import PostgresEngine

import settings
from apphelpers.db.piccolo import BaseTable

db = PostgresEngine(
    config=dict(
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASS,
    )
)


class Book(BaseTable, db=db):
    name = col.Text()
