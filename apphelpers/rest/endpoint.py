from __future__ import annotations


def login_required(func):
    """Auth token is required for this endpoint."""

    func.login_required = True
    return func


def any_group_required(*groups):
    """Any of the mentioned groups is required."""

    def decorator(func):
        func.any_group_required = set(groups)
        return func

    return decorator


def all_groups_required(*groups):
    """All of the mentioned groups are required."""

    def decorator(func):
        func.all_groups_required = set(groups)
        return func

    return decorator


def groups_forbidden(*groups):
    """None of the mentioned groups are allowed."""

    def decorator(func):
        func.groups_forbidden = set(groups)
        return func

    return decorator


def authorizer(authorizer):
    """Custom the authorizer for this endpoint."""

    def decorator(func):
        func.authorizer = authorizer
        return func

    return decorator


def ignore_site_ctx(func):
    """Ignore site context for this endpoint."""

    func.ignore_site_ctx = True
    return func


def not_found_on_none(func):
    """If the return value is None, return HTTP 404 Not Found error."""

    func.not_found_on_none = True
    return func


def response_model(response_model):
    """[FastAPI only] Set response model for this endpoint."""

    def decorator(func):
        func.response_model = response_model
        return func

    return decorator
