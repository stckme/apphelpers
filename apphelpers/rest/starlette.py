def extract_kw(request):
    return (request.args and dict((k, v) for (k, v) in request.args.items())) or \
            request.json or \
            (request.data and json.loads(request.data.decode('utf-8'))) or \
            request.form or \
            {}

