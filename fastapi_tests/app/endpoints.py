from apphelpers.rest import endpoint as ep
from apphelpers.rest.fastapi import (
    json_body,
    user,
    user_id,
)


def echo(word, user=user):
    return "%s:%s" % (user.id, word) if user else word


async def echo_async(word, user=user):
    return "%s:%s" % (user.id, word) if user else word


def echo_post(data=json_body, user=user):
    return "%s:%s" % (user.id, data) if user else data


@ep.login_required
def secure_echo(word, user=user_id):
    return "%s:%s" % (user.id, word) if user else word


@ep.groups_forbidden("noaccess-group")
@ep.all_groups_required("access-group")
def echo_groups(user=user):
    return user.groups


@ep.groups_forbidden("noaccess-group")
@ep.all_groups_required("access-group")
async def echo_groups_async(user=user):
    return user.groups


def add(nums):
    return sum(int(x) for x in nums)


@ep.login_required
def get_my_uid(body=json_body):
    return body["uid"]


@ep.login_required
@ep.not_found_on_none
def get_snake(name=None):
    return name


@ep.login_required
@ep.not_found_on_none
async def get_snake_async(name=None):
    return name


@ep.all_groups_required("access-group")
@ep.groups_forbidden("noaccess-group")
def echo_site_groups(site_id: int, user=user):
    return user.site_groups[site_id]


@ep.all_groups_required("access-group")
@ep.groups_forbidden("noaccess-group")
async def echo_site_groups_async(site_id: int, user=user):
    return user.site_groups[site_id]


def setup_routes(factory):
    factory.get("/echo/{word}")(echo)
    factory.get("/echo-async/{word}")(echo_async)
    factory.post("/echo")(echo_post)

    factory.get("/add")(add)

    factory.get("/secure-echo/{word}")(secure_echo)
    factory.get("/echo-groups")(echo_groups)
    factory.get("/echo-groups-async")(echo_groups_async)

    factory.post("/me/uid")(get_my_uid)

    factory.get("/snakes/{name}")(get_snake)
    factory.get("/snakes-async/{name}")(get_snake_async)

    factory.get("/sites/{site_id}/echo-groups")(echo_site_groups)
    factory.get("/sites/{site_id}/echo-groups-async")(echo_site_groups_async)
