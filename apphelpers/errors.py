from hug import HTTPError
from hug import get_http_status as status

class BaseError(Exception):
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
    def to_dict(self):
        return {'msg': getattr(self, 'msg', ''),
                'code': getattr(self, 'code', None),
                'data': getattr(self, 'data', {})}


class NotFoundError(BaseError):
    code = 404


class SecurityViolation(BaseError):
    pass


class AccessDenied(BaseError):
    msg = 'Access denied'


class ValidationError(BaseError):
    code = 400


class InvalidSessionError(BaseError):
    code = 401
    msg = 'Invalid session'


class ConflictError(BaseError):
    code = 409
    msg = 'Duplicate resource'


class UserAccountExistsError(HTTPError):

    def __init__(self, username):
        description = f'User Account already exists: {username}'
        super().__init__(status.HTTP_109, description=description)