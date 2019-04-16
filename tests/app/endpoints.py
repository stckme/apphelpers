def echo(word):
    return word


def setup_routes(factory):

    factory.get('/echo/{word}')(echo)
    factory.post('/echo')(echo)

    echo.login_required = True
    factory.get('/secure-echo/{word}')(echo)

    # echo.roles_required = []
    # factory.get('/roles-echo/{word}')(echo)

    # ar_handlers = (None, arlib.create, None, arlib.get, arlib.update, None)
    # factory.map_resource('/resttest/', handlers=ar_handlers)
