import hug

import apphelpers.context as contextlib

from apphelpers.db.peewee import dbtransaction
from apphelpers.sessions import SessionDBHandler
from apphelpers.errors import AccessDenied, InvalidSessionError


def phony(f):
    return f


def set_context(token):
    current = {'sid': token}
    contextlib.set_context(**current)
    return current


class APIFactory:

    def __init__(self, router):
        self.router = router
        self.db_tr_wrapper = phony
        self.access_wrapper = phony
        self.secure_router = router.http(requires=hug.authentication.token(set_context))

    def setup_db_transaction(self, db):
        self.db_tr_wrapper = dbtransaction(db)

    def setup_session_db(self, sessiondb_conn):
        """
        redis_conn_params: dict() with below keys
                           (host, port, password, db)
        """
        self.sessions = SessionDBHandler(sessiondb_conn) if sessiondb_conn else None

        def access_wrapper(f):

            def wrapper(request, *args, **kw):
                login_required = getattr(f, 'login_required', None)
                roles_required = getattr(f, 'roles_required', None)

                sid = contextlib.current.sid
                uid, groups = None, []

                if login_required or roles_required:
                    if sid:
                        try:
                            uid, groups = self.sessions.sid2uidgroups(sid)
                        except InvalidSessionError:
                            uid, groups = None, []
                    else:
                        raise AccessDenied(msg='session not found')

                contextlib.set_context(sid=sid, uid=uid, groups=groups)

                if roles_required and not set(contextlib.current.groups).intersection(roles_required):
                    raise AccessDenied(data=dict(groups=groups, roles_required=roles_required))

                return f(*args, **kw)

            return wrapper

        self.access_wrapper = access_wrapper

    def choose_router(self, f):
        login_required = hasattr(f, 'login_required') and f.login_required
        return self.secure_router if login_required else self.router

    def build(self, f):
        for attr in ('login_required', 'roles_required'):
            print(f.__name__, ':', attr, ': ', getattr(f, attr, None))
        return self.access_wrapper(self.db_tr_wrapper(f))

    def get(self, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            return router.get(*a, **k)(self.build(f))
        return _wrapper

    def post(self, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            return router.post(*a, **k)(self.build(f))
        return _wrapper

    def patch(self, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            return router.patch(*a, **k)(self.build(f))
        return _wrapper

    def delete(self, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            return router.delete(*a, **k)(self.build(f))
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
