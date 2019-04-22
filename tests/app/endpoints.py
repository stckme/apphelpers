import hug

from apphelpers.rest.hug import user_id

def echo(word):
    return word


def add(nums: hug.types.multiple):
    return sum(int(x) for x in nums)


def get_my_uid(uid: user_id):
    return uid
get_my_uid.login_required = True


def setup_routes(factory):

    factory.get('/echo/{word}')(echo)
    factory.post('/echo')(echo)

    factory.get('/add')(add)

    echo.login_required = True
    factory.get('/secure-echo/{word}')(echo)

    factory.post('/me/uid')(get_my_uid)

    # echo.roles_required = []
    # factory.get('/roles-echo/{word}')(echo)

    # ar_handlers = (None, arlib.create, None, arlib.get, arlib.update, None)
    # factory.map_resource('/resttest/', handlers=ar_handlers)
