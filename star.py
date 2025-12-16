from starlette.applications import Starlette
from starlette.responses import JSONResponse

import uvicorn

from apphelpers.publishers.starlette import extract_kw


app = Starlette(debug=True)

def extract_kw(request):
    print(dir(request))
    print(request.query_params)
    return (request.query_params() and dict((k, v) for (k, v) in request.args.items())) or \
            request.json or \
            (request.data and json.loads(request.data.decode('utf-8'))) or \
            request.form or \
            {}


@app.route('/', ['GET', 'POST'])
async def homepage(request):
    #print(extract_kw(request))
    return JSONResponse({'hello': 'world'})

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
