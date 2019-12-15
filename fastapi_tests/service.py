import fastapi
from functools import wraps
import sys
import os

sys.path.append(os.getcwd() + '/..')

from apphelpers.rest.fastapi import APIFactory
from app.endpoints import setup_routes

import settings


def make_app():
    api_factory = APIFactory()
    setup_routes(api_factory)

    app = fastapi.FastAPI()
    app.include_router(api_factory.router)
    app.include_router(api_factory.secure_router)
    return app

app = make_app()
