import inspect
from functools import wraps
from typing import Annotated

from converge import settings
from fastapi import APIRouter, Depends, Header, Body, File, Query
from fastapi.routing import APIRoute
from starlette.requests import Request

from apphelpers.db import dbtransaction_ctx, peewee_enabled
from apphelpers.errors.fastapi import (
    BaseError,
    HTTP401Unauthorized,
    HTTP403Forbidden,
    HTTP404NotFound,
    InvalidSessionError,
)
from apphelpers.rest import endpoint as ep
from apphelpers.rest.common import User, notify_honeybadger, phony
from apphelpers.async_sessions import SessionDBHandler

if settings.get("HONEYBADGER_API_KEY"):
    from honeybadger import Honeybadger


def raise_not_found_on_none(f):
    if getattr(f, "not_found_on_none", None) is True:
        if inspect.iscoroutinefunction(f):

            @wraps(f)
            async def async_wrapper(*ar, **kw):
                ret = await f(*ar, **kw)
                if ret is None:
                    raise HTTP404NotFound()
                return ret

            return async_wrapper
        else:

            @wraps(f)
            def wrapper(*ar, **kw):
                ret = f(*ar, **kw)
                if ret is None:
                    raise HTTP404NotFound()
                return ret

            return wrapper
    return f


def honeybadger_wrapper(hb):
    """
    wrapper that executes the function in a try/except
    If an exception occurs, it is first reported to Honeybadger
    """

    def wrapper(f):
        if inspect.iscoroutinefunction(f):

            @wraps(f)
            async def async_f_wrapped(*args, **kw):
                err_to_report = None
                try:
                    return await f(*args, **kw)
                except BaseError as e:
                    if e.report:
                        err_to_report = e
                    raise e
                except Exception as e:
                    err_to_report = e
                    raise e
                finally:
                    if err_to_report:
                        notify_honeybadger(
                            honeybadger=hb,
                            error=err_to_report,
                            func=f,
                            args=args,
                            kwargs=kw,
                        )

            return async_f_wrapped

        else:

            @wraps(f)
            def f_wrapped(*args, **kw):
                err_to_report = None
                try:
                    return f(*args, **kw)
                except BaseError as e:
                    if e.report:
                        err_to_report = e
                    raise e
                except Exception as e:
                    err_to_report = e
                    raise e

                finally:
                    if err_to_report:
                        notify_honeybadger(
                            honeybadger=hb,
                            error=err_to_report,
                            func=f,
                            args=args,
                            kwargs=kw,
                        )

            return f_wrapped

    return wrapper


if peewee_enabled:

    def dbtransaction(db):
        """
        wrapper that make db transactions automic
        note db connections are used only when it is needed (hence there is no
        usual connection open/close)
        """

        def wrapper(f):
            if inspect.iscoroutinefunction(f):

                @wraps(f)
                async def async_wrapper(*ar, **kw):
                    with dbtransaction_ctx(db):
                        return await f(*ar, **kw)

                return async_wrapper
            else:

                @wraps(f)
                async def sync_wrapper(*ar, **kw):
                    with dbtransaction_ctx(db):
                        return f(*ar, **kw)

                return sync_wrapper

        return wrapper

else:
    # for piccolo db
    def dbtransaction(engine, allow_nested=True):
        async def dependency():
            async with dbtransaction_ctx(engine, allow_nested=allow_nested):
                yield

        return Depends(dependency)


async def get_current_user(request: Request):
    return request.state.user if request.state.user.id else None


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
    return await request.body()


async def get_user_agent(request: Request):
    return request.headers.get("USER-AGENT", "")


async def get_user_ip(request: Request):
    return request.headers["X-FORWARDED-FOR"]


raw_body = Annotated[bytes, Depends(get_raw_body)]
json_body = Annotated[dict, Depends(get_json_body)]


class RequestHeaders:
    user_agent = Annotated[str, Depends(get_user_agent)]
    user_ip = Annotated[str, Depends(get_user_ip)]
    domain = Annotated[str, Depends(get_current_domain)]
    custom = Annotated[str, Header()]


class AuthParams:
    user = Annotated[User, Depends(get_current_user)]
    user_id = Annotated[int, Depends(get_current_user_id)]
    user_name = Annotated[str, Depends(get_current_user_name)]
    user_email = Annotated[str, Depends(get_current_user_email)]
    user_mobile = Annotated[str, Depends(get_current_user_mobile)]


class QueryParams:
    list_of_str = Annotated[list[str], Query()]
    list_of_int = Annotated[list[int], Query()]


class BodyParams:
    str = Annotated[str, Body(embed=True)]
    int = Annotated[int, Body(embed=True)]
    file = Annotated[bytes, File()]
    float = Annotated[float, Body(embed=True)]
    bool = Annotated[bool, Body(embed=True)]
    dict = Annotated[dict, Body(embed=True)]
    bytes = Annotated[bytes, Body(embed=True)]
    list_of_str = Annotated[list[str], Body(embed=True)]
    list_of_int = Annotated[list[int], Body(embed=True)]
    list_of_float = Annotated[list[float], Body(embed=True)]
    list_of_bool = Annotated[list[bool], Body(embed=True)]
    list_of_dict = Annotated[list[dict], Body(embed=True)]


class SecureRouter(APIRoute):
    sessions = None
    auth_header_name = None

    @classmethod
    def setup_sessions(cls, sessions: SessionDBHandler):
        cls.sessions = sessions

    @classmethod
    def set_auth_header_name(cls, name: str):
        cls.auth_header_name = name

    def extract_auth_token(self, _request: Request):
        return _request.headers.get(self.auth_header_name)

    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(_request: Request):
            uid, groups, name, email, mobile, site_groups, site_ctx = (
                None,
                [],
                "",
                None,
                None,
                {},
                None,
            )

            token = self.extract_auth_token(_request)
            if token:
                session = await self.sessions.get(  # type: ignore
                    token,
                    [
                        "uid",
                        "name",
                        "groups",
                        "email",
                        "mobile",
                        "site_groups",
                        "site_ctx",
                    ],
                )
                uid, name, groups, email, mobile, site_groups, site_ctx = (
                    session["uid"],
                    session["name"],
                    session["groups"],
                    session["email"],
                    session["mobile"],
                    session["site_groups"],
                    session["site_ctx"],
                )

            _request.state.user = User(
                sid=token,
                id=uid,
                name=name,
                groups=groups,
                email=email,
                mobile=mobile,
                site_groups=site_groups,
                site_ctx=site_ctx,
            )

            return await original_route_handler(_request)

        original_route_handler.__signature__ = inspect.signature(
            original_route_handler
        ).replace(
            parameters=[
                # Use all parameters from handler
                *inspect.signature(original_route_handler).parameters.values(),
                inspect.Parameter(
                    name="_request",
                    kind=inspect.Parameter.VAR_POSITIONAL,
                    annotation=Request,
                ),
            ],
        )
        return custom_route_handler


class SecureByCookieOrHeaderRouter(SecureRouter):
    auth_cookie_name = None

    @classmethod
    def set_auth_cookie_name(cls, cookie_name: str):
        cls.auth_cookie_name = cookie_name

    def extract_auth_token(self, _request: Request):
        return _request.cookies.get(self.auth_cookie_name) or _request.headers.get(
            self.auth_header_name
        )


class Router(SecureRouter):
    def get_route_handler(self):
        original_route_handler = super(SecureRouter, self).get_route_handler()

        async def custom_route_handler(_request: Request):
            uid, groups, name, email, mobile, site_groups, site_ctx = (
                None,
                [],
                "",
                None,
                None,
                {},
                None,
            )

            token = self.extract_auth_token(_request)
            if token:
                try:
                    session = await self.sessions.get(  # type: ignore
                        token,
                        [
                            "uid",
                            "name",
                            "groups",
                            "email",
                            "mobile",
                            "site_groups",
                            "site_ctx",
                        ],
                    )
                    uid, name, groups, email, mobile, site_groups, site_ctx = (
                        session["uid"],
                        session["name"],
                        session["groups"],
                        session["email"],
                        session["mobile"],
                        session["site_groups"],
                        session["site_ctx"],
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
                site_ctx=site_ctx,
            )
            return await original_route_handler(_request)

        original_route_handler.__signature__ = inspect.signature(
            original_route_handler
        ).replace(
            parameters=[
                # Use all parameters from handler
                *inspect.signature(original_route_handler).parameters.values(),
                inspect.Parameter(
                    name="_request",
                    kind=inspect.Parameter.VAR_POSITIONAL,
                    annotation=Request,
                ),
            ],
        )
        return custom_route_handler


class APIFactory:
    def __init__(
        self,
        sessiondb_conn=None,
        urls_prefix="",
        site_identifier=None,
        auth_header_name="Authorization",
        auth_cookie_name="__s",
    ):
        self.access_wrapper = phony
        self.multi_site_enabled = False
        self.site_identifier = site_identifier
        self.urls_prefix = urls_prefix.rstrip("/")
        self.db_tr_wrapper = phony
        self.honeybadger_wrapper = phony

        self.sessions = None
        self.sessiondb_conn = sessiondb_conn
        if site_identifier:
            self.enable_multi_site(site_identifier)
        if sessiondb_conn:
            self.setup_session_db(sessiondb_conn)

        self.router = APIRouter(route_class=Router)
        self.secure_router = APIRouter(route_class=SecureRouter)
        self.secure_by_cookie_or_header_router = APIRouter(
            route_class=SecureByCookieOrHeaderRouter
        )
        self.setup_auth_header(auth_header_name)
        self.setup_auth_cookie(auth_cookie_name)

    def enable_multi_site(self, site_identifier: str):
        self.multi_site_enabled = True
        self.site_identifier = site_identifier
        if self.sessions:
            # if sessions are already set up, we need to reconfigure them
            self.setup_session_db(self.sessiondb_conn)

    def setup_db_transaction(self, db):
        if peewee_enabled:
            self.db_tr_wrapper = dbtransaction(db)
        else:
            self.router.dependencies.append(dbtransaction(db))
            self.secure_router.dependencies.append(dbtransaction(db))
            self.secure_by_cookie_or_header_router.dependencies.append(
                dbtransaction(db)
            )

    def setup_honeybadger_monitoring(self):
        api_key = settings.HONEYBADGER_API_KEY
        if not api_key:
            print("Info: Honeybadger API KEY not found. Honeybadger not set")
            return

        print("Info: Setting up Honeybadger")
        hb = Honeybadger()
        hb.configure(api_key=api_key)
        self.honeybadger_wrapper = honeybadger_wrapper(hb)

    def setup_auth_header(self, auth_header_name: str):
        Router.set_auth_header_name(auth_header_name)
        SecureRouter.set_auth_header_name(auth_header_name)
        SecureByCookieOrHeaderRouter.set_auth_header_name(auth_header_name)

    def setup_auth_cookie(self, auth_cookie_name: str):
        SecureByCookieOrHeaderRouter.set_auth_cookie_name(auth_cookie_name)

    def setup_session_db(self, sessiondb_conn):
        """
        redis_conn_params: dict() with below keys
                           (host, port, password, db)
        """
        self.sessions = SessionDBHandler(sessiondb_conn)
        Router.setup_sessions(self.sessions)
        SecureRouter.setup_sessions(self.sessions)
        SecureByCookieOrHeaderRouter.setup_sessions(self.sessions)

        def access_wrapper(f):
            """
            This is the authentication + authorization part
            """
            login_required = getattr(f, "login_required", None)
            any_group_required = getattr(f, "any_group_required", None)
            all_groups_required = getattr(f, "all_groups_required", None)
            groups_forbidden = getattr(f, "groups_forbidden", None)
            authorizer = getattr(f, "authorizer", None)

            if (
                login_required
                or any_group_required
                or all_groups_required
                or groups_forbidden
                or authorizer
            ):

                @wraps(f)
                async def wrapper(_request, *args, **kw):
                    user = _request.state.user

                    # this is authentication part
                    if not user.id:
                        raise HTTP401Unauthorized("Invalid or expired session")

                    # this is authorization part
                    groups = set(user.groups)

                    if any_group_required and groups.isdisjoint(any_group_required):
                        raise HTTP403Forbidden("Unauthorized access")

                    if all_groups_required and not groups.issuperset(
                        all_groups_required
                    ):
                        raise HTTP403Forbidden("Unauthorized access")

                    if groups_forbidden and groups.intersection(groups_forbidden):
                        raise HTTP403Forbidden("Unauthorized access")

                    if authorizer and not authorizer(user, *args, **kw):
                        raise HTTP403Forbidden("Unauthorized access")

                    return (
                        await f(*args, **kw)
                        if inspect.iscoroutinefunction(f)
                        else f(*args, **kw)
                    )

                f.__signature__ = inspect.signature(f).replace(
                    parameters=[
                        # Use all parameters from handler
                        *inspect.signature(f).parameters.values(),
                        inspect.Parameter(
                            name="_request",
                            kind=inspect.Parameter.VAR_POSITIONAL,
                            annotation=Request,
                        ),
                    ],
                )
            else:
                wrapper = f

            return wrapper

        def multisite_access_wrapper(f):
            """
            This is the authentication + authorization part
            """
            login_required = getattr(f, "login_required", False)
            any_group_required = getattr(f, "any_group_required", False)
            all_groups_required = getattr(f, "all_groups_required", False)
            groups_forbidden = getattr(f, "groups_forbidden", False)
            authorizer = getattr(f, "authorizer", False)

            if (
                login_required
                or any_group_required
                or all_groups_required
                or groups_forbidden
                or authorizer
            ):

                @wraps(f)
                async def wrapper(_request, *args, **kw):
                    user: User = _request.state.user
                    site_id = (
                        int(kw[self.site_identifier])
                        if kw.get(self.site_identifier) is not None
                        else None
                    )

                    # this is authentication part
                    if not user.id:
                        raise HTTP401Unauthorized("Invalid or expired session")

                    # bound site authorization
                    if (
                        user.site_ctx
                        and site_id != user.site_ctx
                        and getattr(f, "ignore_site_ctx", False) is False
                    ):
                        raise HTTP401Unauthorized("Invalid or expired session")

                    # this is authorization part
                    groups = set(user.groups)
                    if site_id:
                        groups = groups.union(user.site_groups.get(site_id, []))

                    if any_group_required and groups.isdisjoint(any_group_required):
                        raise HTTP403Forbidden("Unauthorized access")

                    if all_groups_required and not groups.issuperset(
                        all_groups_required
                    ):
                        raise HTTP403Forbidden("Unauthorized access")

                    if groups_forbidden and groups.intersection(groups_forbidden):
                        raise HTTP403Forbidden("Unauthorized access")

                    if authorizer and not authorizer(user, *args, **kw):
                        raise HTTP403Forbidden("Unauthorized access")

                    return (
                        await f(*args, **kw)
                        if inspect.iscoroutinefunction(f)
                        else f(*args, **kw)
                    )

                f.__signature__ = inspect.signature(f).replace(
                    parameters=[
                        # Use all parameters from handler
                        *inspect.signature(f).parameters.values(),
                        inspect.Parameter(
                            name="_request",
                            kind=inspect.Parameter.VAR_POSITIONAL,
                            annotation=Request,
                        ),
                    ],
                )
            else:
                wrapper = f

            return wrapper

        self.access_wrapper = (
            multisite_access_wrapper if self.multi_site_enabled else access_wrapper
        )

    def choose_router(self, f):
        if getattr(f, "login_required", False):
            return (
                self.secure_by_cookie_or_header_router
                if getattr(f, "auth_by_cookie_or_header", False)
                else self.secure_router
            )
        else:
            return self.router

    def build(self, method, method_args, method_kw, f):
        module = f.__module__.split(".")[-1].strip("_")
        name = f.__name__.strip("_")
        response_model = getattr(f, "response_model", None)
        db_tr_wrapper = (
            phony if getattr(f, "skip_dbtransaction", False) else self.db_tr_wrapper
        )

        if "operation_id" not in method_kw:
            method_kw["operation_id"] = f"{name}_{module}"
        if "name" not in method_kw:
            method_kw["name"] = method_kw["operation_id"]
        if "tags" not in method_kw:
            method_kw["tags"] = [module]

        if response_model is not None and "response_model" not in method_kw:
            method_kw["response_model"] = response_model

        if (
            "response_model" in method_kw
            and "response_model_exclude_unset" not in method_kw
        ):
            method_kw["response_model_exclude_unset"] = True

        print(
            f"{method_args[0]}",
            f"[{method.__name__.upper()}] => {f.__module__}:{f.__name__}",
        )
        m = method(*method_args, **method_kw)
        f = self.access_wrapper(
            self.honeybadger_wrapper(raise_not_found_on_none(db_tr_wrapper(f)))
        )
        # NOTE: ^ wrapper ordering is important. access_wrapper needs request which
        # others don't. If access_wrapper comes late in the order it won't be passed
        # request parameter.
        return m(f)

    def get(self, path, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            full_path = (
                path if path.startswith("/") else f"{self.urls_prefix}/{path}"
            ).rstrip("/")
            args = (full_path,) + a
            return self.build(router.get, args, k, f)

        return _wrapper

    def post(self, path, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            full_path = (
                path if path.startswith("/") else f"{self.urls_prefix}/{path}"
            ).rstrip("/")
            args = (full_path,) + a
            return self.build(router.post, args, k, f)

        return _wrapper

    def put(self, path, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            full_path = (
                path if path.startswith("/") else f"{self.urls_prefix}/{path}"
            ).rstrip("/")
            args = (full_path,) + a
            return self.build(router.put, args, k, f)

        return _wrapper

    def patch(self, path, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            full_path = (
                path if path.startswith("/") else f"{self.urls_prefix}/{path}"
            ).rstrip("/")
            args = (full_path,) + a
            return self.build(router.patch, args, k, f)

        return _wrapper

    def delete(self, path, *a, **k):
        def _wrapper(f):
            router = self.choose_router(f)
            full_path = (
                path if path.startswith("/") else f"{self.urls_prefix}/{path}"
            ).rstrip("/")
            args = (full_path,) + a
            return self.build(router.delete, args, k, f)

        return _wrapper

    def map_resource(self, collection_url, resource=None, handlers=None, id_field="id"):
        if resource:
            raise NotImplementedError("Resource not supported yet")

        collection_url = collection_url.rstrip("/")
        resource_url = f"{collection_url}/{{{id_field}}}"
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


@ep.login_required
def whoami(user: User = AuthParams.user):
    return user.to_dict()
