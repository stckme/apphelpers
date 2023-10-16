import fastapi
from functools import wraps
import sys
import os

sys.path.append(os.getcwd() + "/..")

from apphelpers.rest.fastapi import APIFactory
from fastapi_tests.app.endpoints import setup_routes

import settings


def make_app():
    sessiondb_conn = dict(
        host=settings.SESSIONSDB_HOST,
        port=settings.SESSIONSDB_PORT,
        password=settings.SESSIONSDB_PASSWD,
        db=settings.SESSIONSDB_NO,
    )

    api_factory = APIFactory(sessiondb_conn=sessiondb_conn, site_identifier="site_id")
    setup_routes(api_factory)

    app = fastapi.FastAPI()
    app.include_router(api_factory.router)
    app.include_router(api_factory.secure_router)
    api_factory.setup_session_db(sessiondb_conn)
    return app


app = make_app()
