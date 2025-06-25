from typing import Optional

from fastapi import Query
from pydantic import BaseModel

from apphelpers.rest import endpoint as ep
from apphelpers.rest.fastapi import RequestHeaders, json_body, AuthParams, BodyParams
from fastapi_tests.app.models import Book


def echo(word, user: AuthParams.user):
    return "%s:%s" % (user.id, word) if user else word


async def echo_async(word, user: AuthParams.user):
    return "%s:%s" % (user.id, word) if user else word


def echo_post(data: json_body, user: AuthParams.user):
    return "%s:%s" % (user.id, data) if user else data


def echo_header(x_key: RequestHeaders.custom):
    return x_key


@ep.login_required
@ep.auth_by_cookie_or_header
def secure_echo(word, user_id: AuthParams.user_id):
    return "%s:%s" % (user_id, word) if user_id else word


@ep.groups_forbidden("noaccess-group")
@ep.all_groups_required("access-group")
def echo_groups(user: AuthParams.user):
    return user.groups


@ep.groups_forbidden("noaccess-group")
@ep.all_groups_required("access-group")
async def echo_groups_async(user: AuthParams.user):
    return user.groups


def add(nums):
    return sum(int(x) for x in nums)


@ep.login_required
def get_my_uid(body: json_body):
    return body["uid"]


@ep.login_required
def get_my_uid_unpacked(uid: BodyParams.int = None):
    return uid


@ep.login_required
@ep.response_model(str)
@ep.not_found_on_none
def get_snake(name=None):
    return name


@ep.login_required
@ep.response_model(str)
@ep.not_found_on_none
async def get_snake_async(name=None):
    return name


@ep.all_groups_required("access-group")
@ep.groups_forbidden("noaccess-group")
def echo_site_groups(site_id: int, user: AuthParams.user):
    return user.site_groups[site_id]


@ep.all_groups_required("access-group")
@ep.groups_forbidden("noaccess-group")
async def echo_site_groups_async(site_id: int, user: AuthParams.user):
    return user.site_groups[site_id]


@ep.login_required
async def echo_user_agent_async(user_agent: RequestHeaders.user_agent):
    return user_agent


@ep.login_required
@ep.ignore_site_ctx
async def echo_user_agent_without_site_ctx_async(user_agent: RequestHeaders.user_agent):
    return user_agent


class Fields(BaseModel):
    foo: Optional[int] = None
    bar: Optional[int] = None


@ep.response_model(Fields)
async def get_fields(fields: set = Query(..., default_factory=set)):
    data = {"foo": 1, "bar": None}
    return {k: v for k, v in data.items() if k in fields}


async def add_books(succeed: bool):
    await Book.insert(Book(name="The Pillars of the Earth")).run()
    await Book.insert(Book(name="The Cathedral and the Bazaar")).run()
    if not succeed:
        raise ValueError("Failure")
    await Book.insert(Book(name="The Ego Trick")).run()


async def count_books():
    return await Book.count()


def setup_routes(factory):
    factory.get("/echo/{word}")(echo)
    factory.get("/echo-async/{word}")(echo_async)
    factory.post("/echo")(echo_post)
    factory.get("/echo-header")(echo_header)

    factory.get("/add")(add)

    factory.get("/secure-echo/{word}")(secure_echo)
    factory.get("/echo-groups")(echo_groups)
    factory.get("/echo-groups-async")(echo_groups_async)

    factory.post("/me/uid")(get_my_uid)
    factory.post("/me/uid-unpacked")(get_my_uid_unpacked)

    factory.get("/snakes/{name}")(get_snake)
    factory.get("/snakes-async/{name}")(get_snake_async)

    factory.get("/sites/{site_id}/echo-groups")(echo_site_groups)
    factory.get("/sites/{site_id}/echo-groups-async")(echo_site_groups_async)

    factory.get("/echo-user-agent-async")(echo_user_agent_async)
    factory.get("/echo-user-agent-without-site-ctx-async")(
        echo_user_agent_without_site_ctx_async
    )
    factory.get("/fields")(get_fields)
    factory.get("/count-books")(count_books)
    factory.post("/add-books")(add_books)
