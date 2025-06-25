import asyncio
from unittest import mock
import httpx

import pytest
from requests.exceptions import HTTPError

import apphelpers.sessions as sessionslib
from apphelpers.db.piccolo import destroy_db_from_basetable, setup_db_from_basetable
from apphelpers.errors.fastapi import BaseError
from apphelpers.rest.fastapi import honeybadger_wrapper
from fastapi_tests.app.models import BaseTable

base_url = "http://127.0.0.1:5000/"
echo_url = base_url + "echo"
echo_header_url = base_url + "echo-header"
echo_async_url = base_url + "echo-async"
secure_echo_url = base_url + "secure-echo"
echo_groups_url = base_url + "echo-groups"
echo_groups_async_url = base_url + "echo-groups-async"
echo_site_groups_url = base_url + "sites/{site_id}/echo-groups"
echo_site_groups_async_url = base_url + "sites/{site_id}/echo-groups-async"
pid_path = "tests/run/app.pid"


@pytest.mark.anyio
class TestRest:

    @pytest.fixture(autouse=True)
    async def setup_class(self, sessionsdb: sessionslib.SessionDBHandler):
        await sessionsdb.destroy_all()
        destroy_db_from_basetable(BaseTable)
        setup_db_from_basetable(BaseTable)

    async def test_get(self, client: httpx.AsyncClient):
        word = "hello"
        url = echo_url + "/" + word
        response = await client.get(url, params=dict())
        assert response.json() == word

        word = "hello"
        url = echo_url + "/" + word
        params = {"word": word}
        response = await client.get(url, params=params)
        assert response.json() == word

    async def test_get_async(self, client: httpx.AsyncClient):
        word = "hello"
        url = echo_async_url + "/" + word
        response = await client.get(url, params=dict())
        assert response.json() == word

        word = "hello"
        url = echo_async_url + "/" + word
        params = {"word": word}
        response = await client.get(url, params=params)
        assert response.json() == word

    async def test_get_header(self, client: httpx.AsyncClient):
        x_key = "secret key"
        url = echo_header_url
        headers = {"X-KEY": x_key}
        response = await client.get(url, headers=headers)
        assert response.json() == x_key

    async def test_get_multi_params(self, client: httpx.AsyncClient):
        nums = [3, 5, 8]
        url = base_url + "add"
        params = {"nums": nums}
        response = await client.get(url, params=params)
        assert response.json() == 8  # sum(nums)

    async def test_post(self, client: httpx.AsyncClient):
        word = "hello"
        url = echo_url
        response = await client.post(url, json={"word": word})
        assert response.json()["word"] == word

    async def test_secure_echo(
        self, client: httpx.AsyncClient, sessionsdb: sessionslib.SessionDBHandler
    ):
        word = "hello"
        headers = {"NoAuthorization": "Header"}
        url = secure_echo_url + "/" + word
        resp = await client.get(url, headers=headers)
        assert resp.status_code == 401

        uid = 10000
        d = dict(uid=uid, groups=[])
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        resp = await client.get(url, headers=headers)
        assert resp.status_code == 200
        assert resp.json() == ("%s:%s" % (uid, word))

        cookies = {"__s": sid}
        resp = await client.get(url, cookies=cookies)
        assert resp.status_code == 200
        assert resp.json() == ("%s:%s" % (uid, word))

    async def test_user_id(
        self, client: httpx.AsyncClient, sessionsdb: sessionslib.SessionDBHandler
    ):
        uid = 101
        d = dict(uid=uid, groups=[])
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}

        word = "hello"
        url = echo_url + "/" + word
        resposne = await client.get(url, headers=headers)
        assert resposne.json() == ("%s:%s" % (uid, word))

        url = base_url + "me/uid"

        data = {"uid": None}
        resp = await client.post(url, json=data, headers=headers)
        assert resp.json() == data["uid"]

        data = {"uid": 1}
        resp = await client.post(url, json=data, headers=headers)
        assert resp.json() == data["uid"]

        data = {"uid": uid}
        resp = await client.post(url, json=data, headers=headers)
        assert resp.json() == data["uid"]

        url = base_url + "me/uid-unpacked"

        data = {"uid": None}
        resp = await client.post(url, json=data, headers=headers)
        assert resp.json() == data["uid"]

        data = {"uid": 1}
        resp = await client.post(url, json=data, headers=headers)
        assert resp.json() == data["uid"]

        data = {"uid": uid}
        resp = await client.post(url, json=data, headers=headers)
        assert resp.json() == data["uid"]

    async def test_group_access(
        self, client: httpx.AsyncClient, sessionsdb: sessionslib.SessionDBHandler
    ):
        url = echo_groups_url

        # 1. No group
        uid = 111
        groups = []
        d = dict(uid=uid, groups=groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url, headers=headers)
        assert response.status_code == 403

        # 2. Forbidden group
        uid = 112
        groups = ["noaccess-group"]
        d = dict(uid=uid, groups=groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url, headers=headers)
        assert response.status_code == 403

        # 3. Access group
        uid = 113
        groups = ["access-group"]
        d = dict(uid=uid, groups=groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url, headers=headers)
        assert response.status_code == 200
        assert response.json() == groups

    async def test_group_access_async(
        self, client: httpx.AsyncClient, sessionsdb: sessionslib.SessionDBHandler
    ):
        url = echo_groups_async_url

        # 1. No group
        uid = 111
        groups = []
        d = dict(uid=uid, groups=groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url, headers=headers)
        assert response.status_code == 403

        # 2. Forbidden group
        uid = 112
        groups = ["noaccess-group"]
        d = dict(uid=uid, groups=groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url, headers=headers)
        assert response.status_code == 403

        # 3. Access group
        uid = 113
        groups = ["access-group"]
        d = dict(uid=uid, groups=groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url, headers=headers)
        assert response.status_code == 200
        assert response.json() == groups

    async def test_not_found_on_none(self, client: httpx.AsyncClient):
        url = base_url + "snakes/viper"
        response = await client.get(url)
        assert response.status_code != 404

        url = base_url + "snakes"
        response = await client.get(url)
        assert response.status_code == 404

    async def test_get_fields(self, client: httpx.AsyncClient):
        url = base_url + "fields"
        response = await client.get(url)
        assert response.json() == {}

        url = base_url + "fields?fields=foo"
        response = await client.get(url)
        assert response.json() == {"foo": 1}

        url = base_url + "fields?fields=bar"
        response = await client.get(url)
        assert response.json() == {"bar": None}

        url = base_url + "fields?fields=foo&fields=bar"
        response = await client.get(url)
        assert response.json() == {"foo": 1, "bar": None}

    async def test_site_group_access(
        self, client: httpx.AsyncClient, sessionsdb: sessionslib.SessionDBHandler
    ):
        url = echo_site_groups_url

        # 1. No group
        uid = 1111
        site_id = 2011
        site_groups = {2011: []}
        d = dict(uid=uid, site_groups=site_groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url.format(site_id=site_id), headers=headers)
        assert response.status_code == 403

        # 2. Forbidden group
        uid = 1112
        site_groups = {2011: ["noaccess-group"]}
        d = dict(uid=uid, site_groups=site_groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url.format(site_id=site_id), headers=headers)
        assert response.status_code == 403

        # 3. Access group
        uid = 1113
        site_groups = {2011: ["access-group"]}
        d = dict(uid=uid, site_groups=site_groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url.format(site_id=site_id), headers=headers)
        assert response.status_code == 200
        assert response.json() == site_groups[site_id]

    async def test_site_group_access_async(
        self, client: httpx.AsyncClient, sessionsdb: sessionslib.SessionDBHandler
    ):
        url = echo_site_groups_async_url

        # 1. No group
        uid = 1211
        site_id = 3011
        site_groups = {3011: []}
        d = dict(uid=uid, site_groups=site_groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url.format(site_id=site_id), headers=headers)
        assert response.status_code == 403

        # 2. Forbidden group
        uid = 1212
        site_groups = {3011: ["noaccess-group"]}
        d = dict(uid=uid, site_groups=site_groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url.format(site_id=site_id), headers=headers)
        assert response.status_code == 403

        # 3. Access group
        uid = 1213
        site_groups = {3011: ["access-group"]}
        d = dict(uid=uid, site_groups=site_groups)
        sid = await sessionsdb.create(**d)

        headers = {"Authorization": sid}
        response = await client.get(url.format(site_id=site_id), headers=headers)
        assert response.status_code == 200
        assert response.json() == site_groups[site_id]

    async def test_not_found_on_none_async(self, client: httpx.AsyncClient):
        url = base_url + "snakes-async/viper"
        response = await client.get(url)
        assert response.status_code != 404

        url = base_url + "snakes-async"
        response = await client.get(url)
        assert response.status_code == 404

    async def test_user_agent_async_and_site_ctx(
        self, client: httpx.AsyncClient, sessionsdb: sessionslib.SessionDBHandler
    ):
        url = base_url + "echo-user-agent-async"

        headers = {"Authorization": await sessionsdb.create(uid=1214)}
        response = await client.get(url, headers=headers)
        assert response.status_code == 200
        assert "python-httpx" in response.text

        headers = {"Authorization": await sessionsdb.create(uid=1215, site_ctx=4011)}
        response = await client.get(url, headers=headers)
        assert response.status_code == 401

        url = base_url + "echo-user-agent-without-site-ctx-async"

        headers = {"Authorization": await sessionsdb.create(uid=1214)}
        response = await client.get(url, headers=headers)
        assert response.status_code == 200
        assert "python-httpx" in response.text

        headers = {"Authorization": await sessionsdb.create(uid=1215, site_ctx=4011)}
        response = await client.get(url, headers=headers)
        assert response.status_code == 200
        assert "python-httpx" in response.text

    async def test_piccolo(self, client: httpx.AsyncClient):
        url = base_url + "count-books"
        response = await client.get(url)
        assert response.json() == 0

        url = base_url + "add-books"
        data = {"succeed": True}
        response = await client.post(url, params=data)
        assert response.status_code == 200

        url = base_url + "count-books"
        response = await client.get(url)
        assert response.json() == 3

        url = base_url + "count-books"
        response = await client.get(url)
        assert response.json() == 3

    def test_honeybadger_wrapper(self):

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

        mocked_honeybadger.notify.side_effect = HTTPError(
            response=mock.MagicMock(status_code=403)
        )
        with pytest.raises(RuntimeError):
            asyncio.run(wrapped_worst_endpoint(1))
        # TODO: How to check nested exception?
        assert mocked_honeybadger.notify.call_count == 3

        mocked_honeybadger.notify.side_effect = HTTPError(
            response=mock.MagicMock(status_code=401)
        )
        with pytest.raises(HTTPError):
            asyncio.run(wrapped_worst_endpoint(1))
        # TODO: How to check nested exception?
        assert mocked_honeybadger.notify.call_count == 4
