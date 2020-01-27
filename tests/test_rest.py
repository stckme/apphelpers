import os
import requests
import time
import apphelpers.sessions as sessionslib

from .app.models import globalgroups, sitegroups

from converge import settings


class urls:
    base = 'http://127.0.0.1:8000/'
    echo = base + 'echo'
    echo_for_registered = base + 'secure-echo'
    echo_for_groups = base + 'echo-groups'
    echo_for_sitegroups = base + 'sites/1/echo-groups'


pid_path = 'tests/run/app.pid'

sessiondb_conn = dict(host=settings.SESSIONSDB_HOST,
                      port=settings.SESSIONSDB_PORT,
                      password=settings.SESSIONSDB_PASSWD,
                      db=settings.SESSIONSDB_NO)
sessionsdb = sessionslib.SessionDBHandler(sessiondb_conn)
sessionsdb.destroy_all()


def gunicorn_setup_module():  # not working
    if os.path.exists(pid_path):
        os.remove(pid_path)
    cmd = f'gunicorn tests.service:__hug_wsgi__  -p {pid_path} -D'
    os.system(cmd)
    for i in range(10):
        if os.path.exists(pid_path):
            time.sleep(2)
            break


def gunicorn_teardown_module():
    if os.path.exists(pid_path):
        cmd = f'kill -9 `cat {pid_path}`'
        os.system(cmd)


def test_get():
    word = 'hello'
    url = urls.echo + '/' + word
    assert requests.get(url).json() == word


def test_get_params():
    word = 'hello'
    url = urls.echo + '/' + word
    params = {'word': word}
    assert requests.get(url, params=params).json() == word


def test_get_multi_params():
    nums = [3, 5]
    url = urls.base + 'add'
    params = {'nums': nums}
    assert requests.get(url, params=params).json() == sum(nums)


def test_post():
    word = 'hello'
    url = urls.echo
    assert requests.post(url, json={'word': word}).json() == word


def test_echo_for_registered():
    word = 'hello'
    headers = {'NoAuthorization': 'Header'}
    url = urls.echo_for_registered + '/' + word
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 401


def test_user_id():
    uid = 101
    d = dict(uid=uid, groups=[])
    sid = sessionsdb.create(**d)

    headers = {'Authorization': sid}

    word = 'hello'
    url = urls.echo + '/' + word
    assert requests.get(url, headers=headers).json() == ('%s:%s' % (uid, word))

    url = urls.base + 'me/uid'

    data = {'uid': None}
    resp = requests.post(url, json=data, headers=headers)
    assert resp.json() == uid

    data = {'uid': 1}  # invalid claim
    resp = requests.post(url, json=data, headers=headers)
    assert resp.json() == uid

    data = {'uid': uid}
    resp = requests.post(url, json=data, headers=headers)
    assert resp.json() == uid


def test_group_access():
    # 1. No group
    uid = 111
    groups = []
    d = dict(uid=uid, groups=groups)
    sid = sessionsdb.create(**d)
    url = urls.echo_for_groups

    headers = {'Authorization': sid}
    assert requests.get(url, headers=headers).status_code == 403

    # 2. Forbidden group
    uid = 112
    groups = [globalgroups.forbidden.value]
    d = dict(uid=uid, groups=groups)
    sid = sessionsdb.create(**d)
    url = urls.echo_for_groups

    headers = {'Authorization': sid}
    assert requests.get(url, headers=headers).status_code == 403

    # 3. Access group
    uid = 113
    groups = [globalgroups.privileged.value]
    d = dict(uid=uid, groups=groups)
    sid = sessionsdb.create(**d)

    headers = {'Authorization': sid}
    assert requests.get(url, headers=headers).status_code == 200

    # 4. Other groups
    uid = 112
    groups = [globalgroups.others.value]
    d = dict(uid=uid, groups=groups)
    sid = sessionsdb.create(**d)
    url = urls.echo_for_groups

    headers = {'Authorization': sid}
    assert requests.get(url, headers=headers).status_code == 403


def test_not_found():
    url = urls.base + 'snakes/viper'
    assert requests.get(url).status_code == 404


def test_site_group_access():
    # 1. No group
    uid = 114
    groups = []
    site_groups = {}
    d = dict(uid=uid, groups=groups, site_groups=site_groups)
    sid = sessionsdb.create(**d)
    url = urls.echo_for_sitegroups

    headers = {'Authorization': sid}
    assert requests.get(url, headers=headers).status_code == 403

    # 2. Forbidden group
    uid = 115
    groups = [globalgroups.forbidden.value]
    site_groups = {1: [sitegroups.forbidden.value]}
    d = dict(uid=uid, groups=groups, site_groups=site_groups)
    sid = sessionsdb.create(**d)
    url = urls.echo_for_sitegroups

    headers = {'Authorization': sid}
    assert requests.get(url, headers=headers).status_code == 403

    # 3. Access group
    uid = 116
    groups = [globalgroups.privileged.value]
    site_groups = {1: [sitegroups.privileged.value]}
    d = dict(uid=uid, groups=groups, site_groups=site_groups)
    sid = sessionsdb.create(**d)

    headers = {'Authorization': sid}
    assert requests.get(url, headers=headers).status_code == 200
