import os
import requests
import time

echo_url = 'http://127.0.0.1:8000/echo'
secure_echo_url = 'http://127.0.0.1:8000/secure-echo'


def test_setup():
    os.system('hug -f tests/service.py &')
    time.sleep(2)

def test_get():
    word = 'hello'
    url = echo_url + '/' + word
    assert requests.get(url).json() == word


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

