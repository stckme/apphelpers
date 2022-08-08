import hug

from apphelpers.rest.hug import APIFactory


def echo(word):
    return {"word": word}


def setup_routes(factory):
    factory.get("/echo/{word}")(echo)
    factory.post("/echo")(echo)


def make_app():
    router = hug.route.API(__name__)

    api_factory = APIFactory(router)
    setup_routes(api_factory)


make_app()
# gunicorn tests.services.basic:__hug_wsgi__
