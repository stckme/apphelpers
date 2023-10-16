import requests

import apphelpers.sessions as sessionslib

from converge import settings

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
