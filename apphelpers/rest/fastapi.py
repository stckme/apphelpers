import http
import inspect
from functools import wraps

from starlette.requests import Request
from fastapi import APIRouter, HTTPException, Depends

from fastapi.routing import APIRoute

from apphelpers.db.peewee import dbtransaction
from apphelpers.errors import InvalidSessionError
from apphelpers.sessions import SessionDBHandler
from apphelpers.rest.common import phony, User
from converge import settings


if settings.get("HONEYBADGER_API_KEY"):
    from honeybadger import Honeybadger
    from honeybadger.utils import filter_dict


def raise_not_found_on_none(f):
    if getattr(f, "not_found_on_none", None) == True:

        @wraps(f)
        def wrapper(*ar, **kw):
            ret = f(*ar, **kw)
            if ret is None:
                raise HTTPException(
                    status_code=http.HTTPStatus.NOT_FOUND.value, details="four o four"
                )
            return ret

        return wrapper
    return f


def honeybadger_wrapper(hb):
    """
    wrapper that executes the function in a try/except
    If an exception occurs, it is first reported to Honeybadger
    """

    def wrapper(f):
        @wraps(f)
        def f_wrapped(*args, **kw):
            try:
                ret = f(*args, **kw)
            except Exception as e:
                try:
                    hb.notify(
                        e,
                        context={
                            "func": f.__name__,
                            "args": args,
                            "kwargs": filter_dict(kw, settings.HB_PARAM_FILTERS),
                        },
                    )
                finally:
                    raise e
            return ret

        return f_wrapped

    return wrapper


async def get_current_user(request: Request):
    return request.state.user


async def get_current_user_id(request: Request):
    return request.state.user.id


async def get_current_user_name(request: Request):
    return request.state.user.name


async def get_current_user_email(request: Request):
    return request.state.user.email


async def get_current_user_mobile(request: Request):
    return request.state.user.mobile


async def get_current_domain(request: Request):
    return request.headers["HOST"]


async def get_json_body(request: Request):
    return (
        await request.json()
        if request.headers.get("content-type") == "application/json"
        else {}
    )


async def get_raw_body(request: Request):
    return request.body()


user = Depends(get_current_user)
user_id = Depends(get_current_user_id)
user_name = Depends(get_current_user_name)
user_email = Depends(get_current_user_email)
user_mobile = Depends(get_current_user_mobile)
domain = Depends(get_current_domain)
raw_body = Depends(get_raw_body)
json_body = Depends(get_json_body)


class SecureRouter(APIRoute):
    sessions = None

    @classmethod
    def setup_ssessions(cls, sessions: SessionDBHandler):
        cls.sessions = sessions

    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(_request: Request):
            uid, groups, name, email, mobile, site_groups = None, [], "", None, None, {}

            token = _request.headers.get("Authorization")
            if token:
                try:
                    session = self.sessions.get(
                        token,
                        ["uid", "name", "groups", "email", "mobile", "site_groups"],
                    )
                    uid, name, groups, email, mobile, site_groups = (
                        session["uid"],
                        session["name"],
                        session["groups"],
                        session["email"],
                        session["mobile"],
                        session["site_groups"],
                    )
                except InvalidSessionError:
                    raise HTTPException(
                        status_code=http.HTTPStatus.UNAUTHORIZED.value,
                        details="Invalid or expired session",
                    )

            _request.state.user = User(
                sid=token,
                id=uid,
                name=name,
                groups=groups,
                email=email,
                mobile=mobile,
                site_groups=site_groups,
            )

            return await original_route_handler(_request)

        original_route_handler.__signature__ = inspect.Signature(
            parameters=[
                # Use all parameters from handler
                *inspect.signature(original_route_handler).parameters.values(),
                inspect.Parameter(
                    name="_request",
                    kind=inspect.Parameter.VAR_POSITIONAL,
                    annotation=Request,
                ),
            ],
            return_annotation=inspect.signature(
                original_route_handler
            ).return_annotation,
        )
        return custom_route_handler


class Router(APIRoute):
    sessions = None

    @classmethod
    def setup_ssessions(cls, sessions: SessionDBHandler):
        cls.sessions = sessions

    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(_request: Request):
            uid, groups, name, email, mobile, site_groups = None, [], "", None, None, {}

            token = _request.headers.get("Authorization")
            if token:
                try:
                    session = self.sessions.get(
                        token,
                        ["uid", "name", "groups", "email", "mobile", "site_groups"],
                    )
                    uid, name, groups, email, mobile, site_groups = (
                        session["uid"],
                        session["name"],
                        session["groups"],
                        session["email"],
                        session["mobile"],
                        session["site_groups"],
                    )
                except InvalidSessionError:
                    pass

            _request.state.user = User(
                sid=token,
                id=uid,
                name=name,
                groups=groups,
                email=email,
                mobile=mobile,
                site_groups=site_groups,
            )
            return await original_route_handler(_request)

        original_route_handler.__signature__ = inspect.Signature(
            parameters=[
                # Use all parameters from handler
                *inspect.signature(original_route_handler).parameters.values(),
                inspect.Parameter(
                    name="_request",
                    kind=inspect.Parameter.VAR_POSITIONAL,
                    annotation=Request,
                ),
            ],
            return_annotation=inspect.signature(
                original_route_handler
            ).return_annotation,
        )
        return custom_route_handler


class APIFactory:
    def __init__(self, sessiondb_conn=None, urls_prefix="", site_identifier=None):
        self.db_tr_wrapper = phony
        self.access_wrapper = phony
        self.multi_site_enabled = False
        self.site_identifier = site_identifier
        self.urls_prefix = urls_prefix
        self.honeybadger_wrapper = phony
        if site_identifier:
            self.enable_multi_site(site_identifier)
        self.setup_session_db(sessiondb_conn)
        self.router = APIRouter(route_class=Router)
        self.secure_router = APIRouter(route_class=SecureRouter)

    def enable_multi_site(self, site_identifier: str):
        self.multi_site_enabled = True
        self.site_identifier = site_identifier

    def setup_db_transaction(self, db):
        self.db_tr_wrapper = dbtransaction(db)

    def setup_honeybadger_monitoring(self):
        api_key = settings.HONEYBADGER_API_KEY
        if not api_key:
            print("Info: Honeybadger API KEY not found. Honeybadger not set")
            return

        print("Info: Setting up Honeybadger")
        hb = Honeybadger()
        hb.configure(api_key=api_key)
        self.honeybadger_wrapper = honeybadger_wrapper(hb)

    def setup_session_db(self, sessiondb_conn):
        """
        redis_conn_params: dict() with below keys
                           (host, port, password, db)
        """
        self.sessions = SessionDBHandler(sessiondb_conn)
        Router.setup_ssessions(self.sessions)
        SecureRouter.setup_ssessions(self.sessions)

        def access_wrapper(f):
            """
            This is the authentication + authorization part
            """
            login_required = getattr(f, "login_required", None)
            groups_required = getattr(f, "groups_required", None)
            groups_forbidden = getattr(f, "groups_forbidden", None)
            authorizer = getattr(f, "authorizer", None)

            if login_required or groups_required or groups_forbidden or authorizer:

                @wraps(f)
                async def wrapper(_request, *args, **kw):
                    user = _request.state.user

                    # this is authentication part
                    if not user.id:
                        raise HTTPException(
                            status_code=http.HTTPStatus.UNAUTHORIZED.value,
                            detail="Invalid or expired session",
                        )

                    # this is authorization part
                    groups = set(user.groups)

                    if groups_required and not groups.intersection(groups_required):
                        raise HTTPException(
                            status_code=http.HTTPStatus.FORBIDDEN.value,
                            detail="Unauthorized access",
                        )

                    if groups_forbidden and groups.intersection(groups_forbidden):
                        raise HTTPException(
                            status_code=http.HTTPStatus.FORBIDDEN.value,
                            detail="Unauthorized access",
                        )

                    if authorizer and not authorizer(user, *args, **kw):
                        raise HTTPException(
                            status_code=http.HTTPStatus.FORBIDDEN.value,
                            detail="Unauthorized access",
                        )

                    return (
                        await f(*args, **kw)
                        if inspect.iscoroutinefunction(f)
                        else f(*args, **kw)
                    )

                f.__signature__ = inspect.Signature(
                    parameters=[
                        # Use all parameters from handler
                        *inspect.signature(f).parameters.values(),
                        inspect.Parameter(
                            name="_request",
                            kind=inspect.Parameter.VAR_POSITIONAL,
                            annotation=Request,
                        ),
                    ],
                    return_annotation=inspect.signature(f).return_annotation,
                )
            else:
                wrapper = f

            return wrapper

        def multisite_access_wrapper(f):
            """
            This is the authentication + authorization part
            """
            login_required = getattr(f, "login_required", None)
            groups_required = getattr(f, "groups_required", None)
            groups_forbidden = getattr(f, "groups_forbidden", None)
            authorizer = getattr(f, "authorizer", None)

            if login_required or groups_required or groups_forbidden or authorizer:

                @wraps(f)
                async def wrapper(_request, *args, **kw):

                    user = _request.state.user

                    # this is authentication part
                    if not user.id:
                        raise HTTPException(
                            status_code=http.HTTPStatus.UNAUTHORIZED.value,
                            detail="Invalid or expired session",
                        )

                    # this is authorization part
                    groups = set(user.groups)
                    if self.site_identifier in kw:
                        site_id = int(kw[self.site_identifier])
                        groups = groups.union(user.site_groups.get(site_id, []))

                    if groups_required and not groups.intersection(groups_required):
                        raise HTTPException(
                            status_code=http.HTTPStatus.FORBIDDEN.value,
                            detail="Unauthorized access",
                        )

                    if groups_forbidden and groups.intersection(groups_forbidden):
                        raise HTTPException(
                            status_code=http.HTTPStatus.FORBIDDEN.value,
                            detail="Unauthorized access",
                        )

                    if authorizer and not authorizer(user, *args, **kw):
                        raise HTTPException(
                            status_code=http.HTTPStatus.FORBIDDEN.value,
                            detail="Unauthorized access",
                        )

                    return (
                        await f(*args, **kw)
                        if inspect.iscoroutinefunction(f)
                        else f(*args, **kw)
                    )

                f.__signature__ = inspect.Signature(
                    parameters=[
                        # Use all parameters from handler
                        *inspect.signature(f).parameters.values(),
                        inspect.Parameter(
                            name="_request",
                            kind=inspect.Parameter.VAR_POSITIONAL,
                            annotation=Request,
                        ),
                    ],
                    return_annotation=inspect.signature(f).return_annotation,
                )
            else:
                wrapper = f

            return wrapper

        self.access_wrapper = (
            multisite_access_wrapper if self.multi_site_enabled else access_wrapper
        )

    def choose_router(self, f):
        login_required = hasattr(f, "login_required") and f.login_required
        return self.secure_router if login_required else self.router

    def build(self, method, method_args, method_kw, f):
        print(
            f"{method_args[0]} [{method.__name__.upper()}] => {f.__module__}:{f.__name__}"
        )
        m = method(*method_args, **method_kw)
        f = self.access_wrapper(
            self.honeybadger_wrapper(self.db_tr_wrapper(raise_not_found_on_none(f)))
        )
        # NOTE: ^ wrapper ordering is important. access_wrapper needs request which
        # others don't. If access_wrapper comes late in the order it won't be passed
        # request parameter.
        return m(f)

    def get(self, path, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            args = (path if path.startswith("/") else (self.urls_prefix + path),) + a
            return self.build(router.get, args, k, f)

        return _wrapper

    def post(self, path, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            args = (path if path.startswith("/") else (self.urls_prefix + path),) + a
            return self.build(router.post, args, k, f)

        return _wrapper

    def put(self, path, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            args = (path if path.startswith("/") else (self.urls_prefix + path),) + a
            return self.build(router.put, args, k, f)

        return _wrapper

    def patch(self, path, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            args = (path if path.startswith("/") else (self.urls_prefix + path),) + a
            return self.build(router.patch, args, k, f)

        return _wrapper

    def delete(self, path, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            args = (path if path.startswith("/") else (self.urls_prefix + path),) + a
            return self.build(router.delete, args, k, f)

        return _wrapper

    def map_resource(self, collection_url, resource=None, handlers=None, id_field="id"):
        if resource:
            raise NotImplementedError("Resource not supported yet")

        resource_url = collection_url + "{" + id_field + "}"
        assert isinstance(handlers, (list, tuple)), "handlers should be list or tuple"
        (
            get_collection,
            add_resource,
            replace_resource,
            get_resource,
            update_resource,
            delete_resource,
        ) = handlers

        if get_collection:
            self.get(collection_url)(get_collection)
        if add_resource:
            self.post(collection_url)(add_resource)
        if replace_resource:
            self.put(resource_url)(replace_resource)
        if get_resource:
            self.get(resource_url)(get_resource)
        if update_resource:
            self.patch(resource_url)(update_resource)
        if delete_resource:
            self.delete(resource_url)(delete_resource)
