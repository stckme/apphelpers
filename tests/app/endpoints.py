from enum import Enum
import hug
import hug.directives

from apphelpers.rest.hug import user_id

from tests.app.models import globalgroups, sitegroups


def echo(word, user: hug.directives.user=None):
    return '%s:%s' % (user.id, word) if user else word


def secure_echo(word, user: hug.directives.user=None):
    return '%s:%s' % (user.id, word) if user else word
secure_echo.login_required = True


def echo_groups(user: hug.directives.user=None):
    return user.groups
echo_groups.groups_required = [globalgroups.privileged.value]
echo_groups.groups_forbidden = [globalgroups.forbidden.value]


def add(nums: hug.types.multiple):
    return sum(int(x) for x in nums)


def get_my_uid(uid: user_id):
    return uid
get_my_uid.login_required = True


def get_snake(name):
    return None
get_snake.not_found_on_none = True


def secure_multisite_echo(word, user: hug.directives.user=None):
    return '%s:%s' % (user.id, word) if user else word
secure_echo.login_required = True


def echo_multisite_groups(site_id: int, user: hug.directives.user=None):
    return user.groups
echo_multisite_groups.groups_required = [sitegroups.privileged.value]
echo_multisite_groups.groups_forbidden = [sitegroups.forbidden.value]


def setup_routes(factory):

    factory.get('/echo/{word}')(echo)
    factory.post('/echo')(echo)

    factory.get('/add')(add)

    factory.get('/secure-echo/{word}')(secure_echo)
    factory.get('/echo-groups')(echo_groups)

    factory.post('/me/uid')(get_my_uid)

    factory.get('/snakes/{name}')(get_snake)

    factory.get('/sites/{site_id}/secure-echo/{word}')(secure_multisite_echo)
    factory.get('/sites/{site_id}/echo-groups')(echo_multisite_groups)

    # ar_handlers = (None, arlib.create, None, arlib.get, arlib.update, None)
    # factory.map_resource('/resttest/', handlers=ar_handlers)
