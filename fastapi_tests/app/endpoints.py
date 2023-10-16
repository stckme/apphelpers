from apphelpers.rest.fastapi import user, user_id, json_body


def echo(word, user=user):
    return '%s:%s' % (user.id, word) if user else word


async def echo_async(word, user=user):
    return '%s:%s' % (user.id, word) if user else word


def echo_post(data=json_body, user=user):
    return '%s:%s' % (user.id, data) if user else data


def secure_echo(word, user=user_id):
    return '%s:%s' % (user.id, word) if user else word
secure_echo.login_required = True


def echo_groups(user=user):
    return user.groups
echo_groups.groups_required = ['access-group']
echo_groups.groups_forbidden = ['forbidden-group']


async def echo_groups_async(user=user):
    return user.groups
echo_groups_async.groups_required = ['access-group']
echo_groups_async.groups_forbidden = ['forbidden-group']


def add(nums):
    return sum(int(x) for x in nums)


def get_my_uid(body=json_body):
    return body["uid"]
get_my_uid.login_required = True


def get_snake(name=None):
    return name
get_snake.not_found_on_none = True
get_snake.login_required = True


async def get_snake_async(name=None):
    return name
get_snake.not_found_on_none = True
get_snake.login_required = True


def echo_site_groups(site_id: int, user=user):
    return user.site_groups[site_id]
echo_site_groups.groups_required = ['access-group']
echo_site_groups.groups_forbidden = ['forbidden-group']


async def echo_site_groups_async(site_id: int, user=user):
    return user.site_groups[site_id]
echo_site_groups_async.groups_required = ['access-group']
echo_site_groups_async.groups_forbidden = ['forbidden-group']


def setup_routes(factory):
    factory.get('/echo/{word}')(echo)
    factory.get('/echo-async/{word}')(echo_async)
    factory.post('/echo')(echo_post)

    factory.get('/add')(add)

    factory.get('/secure-echo/{word}')(secure_echo)
    factory.get('/echo-groups')(echo_groups)
    factory.get('/echo-groups-async')(echo_groups_async)

    factory.post('/me/uid')(get_my_uid)

    factory.get('/snakes/{name}')(get_snake)
    factory.get('/snakes-async/{name}')(get_snake_async)

    factory.get('/sites/{site_id}/echo-groups')(echo_site_groups)
    factory.get('/sites/{site_id}/echo-groups-async')(echo_site_groups_async)
