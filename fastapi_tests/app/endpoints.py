from starlette.requests import Request
from fastapi import Depends, FastAPI, Header, HTTPException
from apphelpers.rest.fastapi import get_current_user_id


def echo(word, user):
    return '%s:%s' % (user.id, word) if user else word


def secure_echo(word, user):
    return '%s:%s' % (user.id, word) if user else word
secure_echo.login_required = True


def echo_groups(user):
    return user.groups
echo_groups.groups_required = ['access-group']
echo_groups.groups_forbidden = ['forbidden-group']


def add(nums):
    return sum(int(x) for x in nums)


def get_my_uid(uid):
    return uid
get_my_uid.login_required = True


def get_snake(name, user=Depends(get_current_user_id)):
    return name
get_snake.not_found_on_none = True
get_snake.login_required = True


def setup_routes(factory):
    factory.get('/echo/{word}')(echo)
    factory.post('/echo')(echo)

    factory.get('/add')(add)

    factory.get('/secure-echo/{word}')(secure_echo)
    factory.get('/echo-groups')(echo_groups)

    factory.post('/me/uid')(get_my_uid)

    factory.get('/snakes/{name}')(get_snake)
