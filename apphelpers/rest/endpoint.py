from __future__ import annotations


def login_required(func):
    func.login_required = True
    return func


def any_group_required(*groups):
    def decorator(func):
        func.any_group_required = set(groups)
        return func

    return decorator


def all_groups_required(*groups):
    def decorator(func):
        func.all_groups_required = set(groups)
        return func

    return decorator


def groups_forbidden(*groups):
    def decorator(func):
        func.groups_forbidden = set(groups)
        return func

    return decorator


def authorizer(authorizer):
    def decorator(func):
        func.authorizer = authorizer
        return func

    return decorator


def not_found_on_none(func):
    func.not_found_on_none = True
    return func
