import asyncio
from unittest import mock

import pytest
import requests
from converge import settings

import apphelpers.sessions as sessionslib
from apphelpers.db.piccolo import destroy_db_from_basetable, setup_db_from_basetable
from apphelpers.errors.fastapi import BaseError
from apphelpers.rest.fastapi import honeybadger_wrapper
from fastapi_tests.app.models import BaseTable

base_url = "http://127.0.0.1:5000/"
echo_url = base_url + "echo"
echo_async_url = base_url + "echo-async"
secure_echo_url = base_url + "secure-echo"
echo_groups_url = base_url + "echo-groups"
echo_groups_async_url = base_url + "echo-groups-async"
echo_site_groups_url = base_url + "sites/{site_id}/echo-groups"
echo_site_groups_async_url = base_url + "sites/{site_id}/echo-groups-async"
pid_path = "tests/run/app.pid"

sessiondb_conn = dict(
    host=settings.SESSIONSDB_HOST,
    port=settings.SESSIONSDB_PORT,
    password=settings.SESSIONSDB_PASSWD,
    db=settings.SESSIONSDB_NO,
)
sessionsdb = sessionslib.SessionDBHandler(sessiondb_conn)


def setup_module():
    sessionsdb.destroy_all()
    destroy_db_from_basetable(BaseTable)
    setup_db_from_basetable(BaseTable)


def teardown_module():
    sessionsdb.destroy_all()
    destroy_db_from_basetable(BaseTable)


def test_get():
    word = "hello"
    url = echo_url + "/" + word
    assert requests.get(url, params=dict()).json() == word

    word = "hello"
    url = echo_url + "/" + word
    params = {"word": word}
    assert requests.get(url, params=params).json() == word


def test_get_async():
    word = "hello"
    url = echo_async_url + "/" + word
    assert requests.get(url, params=dict()).json() == word

    word = "hello"
    url = echo_async_url + "/" + word
    params = {"word": word}
    assert requests.get(url, params=params).json() == word


def test_get_multi_params():
    nums = [3, 5, 8]
    url = base_url + "add"
    params = {"nums": nums}
    assert requests.get(url, params=params).json() == 8  # sum(nums)


def test_post():
    word = "hello"
    url = echo_url
    assert requests.post(url, json={"word": word}).json()["word"] == word


def test_secure_echo():
    word = "hello"
    headers = {"NoAuthorization": "Header"}
    url = secure_echo_url + "/" + word
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 401


def test_user_id():
    uid = 101
    d = dict(uid=uid, groups=[])
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}

    word = "hello"
    url = echo_url + "/" + word
    assert requests.get(url, headers=headers).json() == ("%s:%s" % (uid, word))

    url = base_url + "me/uid"

    data = {"uid": None}
    resp = requests.post(url, json=data, headers=headers)
    assert resp.json() == data["uid"]

    data = {"uid": 1}  # invalid claim
    resp = requests.post(url, json=data, headers=headers)
    assert resp.json() == data["uid"]

    data = {"uid": uid}
    resp = requests.post(url, json=data, headers=headers)
    assert resp.json() == data["uid"]


def test_group_access():
    url = echo_groups_url

    # 1. No group
    uid = 111
    groups = []
    d = dict(uid=uid, groups=groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url, headers=headers).status_code == 403

    # 2. Forbidden group
    uid = 112
    groups = ["noaccess-group"]
    d = dict(uid=uid, groups=groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url, headers=headers).status_code == 403

    # 3. Access group
    uid = 113
    groups = ["access-group"]
    d = dict(uid=uid, groups=groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url, headers=headers).status_code == 200
    assert requests.get(url, headers=headers).json() == groups


def test_group_access_async():
    url = echo_groups_async_url

    # 1. No group
    uid = 111
    groups = []
    d = dict(uid=uid, groups=groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url, headers=headers).status_code == 403

    # 2. Forbidden group
    uid = 112
    groups = ["noaccess-group"]
    d = dict(uid=uid, groups=groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url, headers=headers).status_code == 403

    # 3. Access group
    uid = 113
    groups = ["access-group"]
    d = dict(uid=uid, groups=groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url, headers=headers).status_code == 200
    assert requests.get(url, headers=headers).json() == groups


def test_not_found_on_none():
    url = base_url + "snakes/viper"
    assert requests.get(url).status_code != 404

    url = base_url + "snakes"
    assert requests.get(url).status_code == 404


def test_get_fields():
    url = base_url + "fields"
    assert requests.get(url).json() == {}

    url = base_url + "fields?fields=foo"
    assert requests.get(url).json() == {"foo": 1}

    url = base_url + "fields?fields=bar"
    assert requests.get(url).json() == {"bar": None}

    url = base_url + "fields?fields=foo&fields=bar"
    assert requests.get(url).json() == {"foo": 1, "bar": None}


def test_site_group_access():
    url = echo_site_groups_url

    # 1. No group
    uid = 1111
    site_id = 2011
    site_groups = {2011: []}
    d = dict(uid=uid, site_groups=site_groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url.format(site_id=site_id), headers=headers).status_code == 403

    # 2. Forbidden group
    uid = 1112
    site_groups = {2011: ["noaccess-group"]}
    d = dict(uid=uid, site_groups=site_groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url.format(site_id=site_id), headers=headers).status_code == 403

    # 3. Access group
    uid = 1113
    site_groups = {2011: ["access-group"]}
    d = dict(uid=uid, site_groups=site_groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url.format(site_id=site_id), headers=headers).status_code == 200
    assert (
        requests.get(url.format(site_id=site_id), headers=headers).json()
        == site_groups[site_id]
    )


def test_site_group_access_async():
    url = echo_site_groups_async_url

    # 1. No group
    uid = 1211
    site_id = 3011
    site_groups = {3011: []}
    d = dict(uid=uid, site_groups=site_groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url.format(site_id=site_id), headers=headers).status_code == 403

    # 2. Forbidden group
    uid = 1212
    site_groups = {3011: ["noaccess-group"]}
    d = dict(uid=uid, site_groups=site_groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url.format(site_id=site_id), headers=headers).status_code == 403

    # 3. Access group
    uid = 1213
    site_groups = {3011: ["access-group"]}
    d = dict(uid=uid, site_groups=site_groups)
    sid = sessionsdb.create(**d)

    headers = {"Authorization": sid}
    assert requests.get(url.format(site_id=site_id), headers=headers).status_code == 200
    assert (
        requests.get(url.format(site_id=site_id), headers=headers).json()
        == site_groups[site_id]
    )


def test_not_found_on_none_async():
    url = base_url + "snakes-async/viper"
    assert requests.get(url).status_code != 404

    url = base_url + "snakes-async"
    assert requests.get(url).status_code == 404


def test_user_agent_async_and_site_ctx():
    url = base_url + "echo-user-agent-async"

    headers = {"Authorization": sessionsdb.create(uid=1214)}
    response = requests.get(url, headers=headers)
    assert response.status_code == 200
    assert "python-requests" in response.text

    headers = {"Authorization": sessionsdb.create(uid=1215, site_ctx=4011)}
    response = requests.get(url, headers=headers)
    assert response.status_code == 401

    url = base_url + "echo-user-agent-without-site-ctx-async"

    headers = {"Authorization": sessionsdb.create(uid=1214)}
    response = requests.get(url, headers=headers)
    assert response.status_code == 200
    assert "python-requests" in response.text

    headers = {"Authorization": sessionsdb.create(uid=1215, site_ctx=4011)}
    response = requests.get(url, headers=headers)
    assert response.status_code == 200
    assert "python-requests" in response.text


def test_piccolo():
    url = base_url + "count-books"
    assert requests.get(url).json() == 0

    url = base_url + "add-books"
    data = {"succeed": True}
    assert requests.post(url, params=data).status_code == 200

    url = base_url + "count-books"
    assert requests.get(url).json() == 3

    url = base_url + "add-books"
    data = {"succeed": False}
    assert requests.post(url, params=data).status_code == 500

    url = base_url + "count-books"
    assert requests.get(url).json() == 3


def test_honeybadger_wrapper():

    mocked_honeybadger = mock.MagicMock()
    wrapper = honeybadger_wrapper(mocked_honeybadger)

    def good_endpoint(foo):
        return foo

    class IgnorableError(BaseError):
        report = False

    async def bad_endpoint(foo):
        raise IgnorableError()

    async def worse_endpoint(foo, password):
        raise BaseError()

    async def worst_endpoint(foo):
        raise RuntimeError()

    wrapped_good_endpoint = wrapper(good_endpoint)
    wrapped_bad_endpoint = wrapper(bad_endpoint)
    wrapped_worse_endpoint = wrapper(worse_endpoint)
    wrapped_worst_endpoint = wrapper(worst_endpoint)

    assert wrapped_good_endpoint(1) == 1
    assert not mocked_honeybadger.notify.called

    with pytest.raises(IgnorableError):
        asyncio.run(wrapped_bad_endpoint(1))
    assert not mocked_honeybadger.notify.called

    with pytest.raises(BaseError) as e:
        asyncio.run(wrapped_worse_endpoint(1, password="secret"))
    mocked_honeybadger.notify.assert_called_once_with(
        e.value,
        context={
            "func": "worse_endpoint",
            "args": (1,),
            "kwargs": {"password": "[FILTERED]"},
        },
    )
    assert mocked_honeybadger.notify.call_count == 1

    with pytest.raises(RuntimeError):
        asyncio.run(wrapped_worst_endpoint(1))
    assert mocked_honeybadger.notify.call_count == 2
