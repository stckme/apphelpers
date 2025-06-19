import os
import sys

import fastapi

sys.path.append(os.getcwd() + "/..")

import settings  # noqa E402
from apphelpers.rest.fastapi import APIFactory  # noqa E402
from fastapi_tests.app.endpoints import setup_routes  # noqa E402
from fastapi_tests.app.models import db  # noqa E402


def make_app():
    sessiondb_conn = dict(
        host=settings.SESSIONSDB_HOST,
        port=settings.SESSIONSDB_PORT,
        password=settings.SESSIONSDB_PASSWD,
        db=settings.SESSIONSDB_NO,
    )

    api_factory = APIFactory(sessiondb_conn=sessiondb_conn, site_identifier="site_id")
    api_factory.setup_db_transaction(db)
    setup_routes(api_factory)

    app = fastapi.FastAPI()
    app.include_router(api_factory.router)
    app.include_router(api_factory.secure_router)
    app.include_router(api_factory.secure_by_cookie_or_header_router)
    api_factory.setup_session_db(sessiondb_conn)
    return app


app = make_app()
