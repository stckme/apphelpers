import os
import requests
import time

import apphelpers.sessions as sessionslib

from converge import settings

base_url = 'http://127.0.0.1:8000/'
echo_url = base_url + 'echo'
secure_echo_url = base_url + 'secure-echo'
pid_path = 'tests/run/app.pid'

sessiondb_conn = dict(host=settings.SESSIONSDB_HOST,
                      port=settings.SESSIONSDB_PORT,
                      password=settings.SESSIONSDB_PASSWD,
                      db=settings.SESSIONSDB_NO)
sessionsdb = sessionslib.SessionDBHandler(sessiondb_conn)


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
    url = echo_url + '/' + word
    assert requests.get(url).json() == word


def test_get_params():
    word = 'hello'
    url = echo_url + '/' + word
    params = {'word': word}
    assert requests.get(url, params=params).json() == word


def test_get_multi_params():
    nums = [3, 5]
    url = base_url + 'add'
    params = {'nums': nums}
    assert requests.get(url, params=params).json() == sum(nums)


def test_post():
    word = 'hello'
    url = echo_url
    assert requests.post(url, json={'word': word}).json() == word


def test_secure_echo():
    word = 'hello'
    headers = {'No Authorization': 'Header'}
    url = secure_echo_url + '/' + word
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 401


def test_user_id():
    uid = 101
    d = dict(uid=uid, groups=[])
    sid = sessionsdb.create(**d)

    headers = {'Authorization': sid}
    url = base_url + 'me/uid'

    data = {'uid': None}
    resp = requests.post(url, json=data, headers=headers)
    assert resp.json() == uid

    data = {'uid': 1}  # invalid claim
    resp = requests.post(url, json=data, headers=headers)
    assert resp.json() == uid

    data = {'uid': uid}
    resp = requests.post(url, json=data, headers=headers)
    assert resp.json() == uid
