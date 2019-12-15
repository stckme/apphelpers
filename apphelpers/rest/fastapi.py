from dataclasses import dataclass, asdict
from functools import wraps
from falcon import HTTPUnauthorized, HTTPForbidden, HTTPNotFound

from starlette.requests import Request
from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute

from apphelpers.db.peewee import dbtransaction
from apphelpers.errors import InvalidSessionError
from apphelpers.sessions import SessionDBHandler


def phony(f):
    return f


def raise_not_found_on_none(f):
    if getattr(f, 'not_found_on_none', None) == True:
        @wraps(f)
        def wrapper(*a, **k):
            ret = f(*a, **k)
            if ret is None:
                raise HTTPNotFound('four o four')
            return ret
        return wrapper
    return f


def get_current_user(request: Request):
    return request.state.user


def get_current_user_id(request: Request):
    return request.state.user.id


def get_current_user_name(request: Request):
    return request.state.user.name


def get_current_user_email(request: Request):
    return request.state.user.email


@dataclass
class User:
    sid: str=None
    id: int=None
    name: str=None
    groups: tuple=()
    email: str=None

    def to_dict(self):
        return asdict(self)

    def __bool__(self):
        return bool(self.id)


class SecureRouter(APIRoute):

    def get_route_handler(self):
        original_route_handler = super().get_route_handler()
        async def custom_route_handler(request: Request):

            uid, groups, name, email = None, [], '', None

            token = request.headers.get('Authorization')
            if token:
                try:
                    #session = self.sessions.get(token, ['uid', 'name', 'groups', 'email'])
                    #uid, name, groups, email = session['uid'], session['name'], session['groups'], session['email']
                    pass
                except InvalidSessionError:
                    raise HTTPUnauthorized('Invalid or expired session')

                request.state.user = User(sid=token, id=uid, name=name, groups=groups, email=email)

            return await original_route_handler(request)
        return custom_route_handler



class Router(APIRoute):

    def get_route_handler(self):
        original_route_handler = super().get_route_handler()
        async def custom_route_handler(request: Request):
            return await original_route_handler(request)
        return custom_route_handler


class APIFactory:

    def __init__(self):
        self.router = APIRouter(route_class=Router)
        self.secure_router = APIRouter(route_class=SecureRouter)
        #self.secure_router.sessions = SessionDBHandler(sessiondb_conn)
        self.db_tr_wrapper = phony
        self.access_wrapper = phony

    def setup_db_transaction(self, db):
        self.db_tr_wrapper = dbtransaction(db)

    def choose_router(self, f):
        login_required = hasattr(f, 'login_required') and f.login_required
        return self.secure_router if login_required else self.router

    def build(self, method, method_args, method_kw, f):
        print(f'{method_args[0]} [{method.__name__.upper()}] => {f.__module__}:{f.__name__}')
        m = method(*method_args, **method_kw)
        f = raise_not_found_on_none(self.access_wrapper(self.db_tr_wrapper(f)))
        return m(f)

    def get(self, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            return self.build(router.get, a, k, f)
        return _wrapper

    def post(self, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            return self.build(router.post, a, k, f)
        return _wrapper

    def patch(self, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            return self.build(router.patch, a, k, f)
        return _wrapper

    def delete(self, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            return self.build(router.delete, a, k, f)
        return _wrapper

    def map_resource(self, url, resource=None, handlers=None, id_field='id'):
        if resource:
            raise NotImplementedError("Resource not supported yet")

        collection_url = (self.urls_prefix + url) if not url.startswith('/') else url
        resource_url = collection_url + '{' + id_field + '}'

        assert isinstance(handlers, (list, tuple)), "handlers should be list or tuple"
        get_collection, add_resource, replace_resource, get_resource, update_resource, delete_resource = handlers

        if get_collection:
            self.get(collection_url)(get_collection)
        if add_resource:
            self.post(collection_url)(add_resource)
        if replace_resource:
            self.put(resource_url)(replace_resource)
        if get_resource:
            # get_resource_wrapped = get_or_not_found(get_resource)
            self.get(resource_url)(get_resource)
        if update_resource:
            self.patch(resource_url)(update_resource)
        if delete_resource:
            self.delete(resource_url)(delete_resource)
