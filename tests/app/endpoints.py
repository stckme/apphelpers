import hug
import hug.directives

from apphelpers.rest.hug import user_id

def echo(word, user: hug.directives.user=None):
    return '%s:%s' % (user.id, word) if user else word


def secure_echo(word, user: hug.directives.user=None):
    return '%s:%s' % (user.id, word) if user else word
secure_echo.login_required = True


def add(nums: hug.types.multiple):
    return sum(int(x) for x in nums)


def get_my_uid(uid: user_id):
    return uid
get_my_uid.login_required = True


def setup_routes(factory):

    factory.get('/echo/{word}')(echo)
    factory.post('/echo')(echo)

    factory.get('/add')(add)

    factory.get('/secure-echo/{word}')(secure_echo)

    factory.post('/me/uid')(get_my_uid)

    # echo.roles_required = []
    # factory.get('/roles-echo/{word}')(echo)

    # ar_handlers = (None, arlib.create, None, arlib.get, arlib.update, None)
    # factory.map_resource('/resttest/', handlers=ar_handlers)
