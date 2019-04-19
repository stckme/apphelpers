import os
import requests
import time

base_url = 'http://0.0.0.0:8000/'
echo_url = base_url + 'echo'
secure_echo_url = base_url + 'secure-echo'
pid_path = 'tests/run/app.pid'


def setup_module():
    if os.path.exists(pid_path):
        os.remove(pid_path)
    cmd = f'gunicorn tests.service:__hug_wsgi__  -p {pid_path} -D'
    os.system(cmd)
    for i in range(10):
        if os.path.exists(pid_path):
            time.sleep(2)
            break


def teardown_module():
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
    headers = {'Authorization': 'Invalid session id'}
    url = secure_echo_url + '/' + word
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 401
