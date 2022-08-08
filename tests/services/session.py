import hug
import settings

from apphelpers.rest.hug import APIFactory


def echo(word):
    return {"word": word}


def protected_echo(word):
    return {"word": word}


protected_echo.login_required = True


def setup_routes(factory):
    factory.get("/echo/{word}")(echo)
    factory.post("/echo")(echo)
    factory.get("/p/echo/{word}")(echo)
    factory.post("/p/echo")(echo)


def make_app():
    router = hug.route.API(__name__)
    api_factory = APIFactory(router)
    sessiondb_conn = dict(
        host=settings.SESSIONSDB_HOST,
        port=settings.SESSIONSDB_PORT,
        password=settings.SESSIONSDB_PASSWD,
        db=settings.SESSIONSDB_NO,
    )
    api_factory.setup_session_db(sessiondb_conn)
    setup_routes(api_factory)


make_app()
# gunicorn tests.services.session:__hug_wsgi__
