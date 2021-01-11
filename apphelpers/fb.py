import os
from requests_oauthlib import OAuth2Session

from converge import settings
from errors import UserAccountExistsError

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'True'


def fetch_info(access_token):
    session = OAuth2Session(token={'access_token': access_token})
    info_url = 'https://graph.facebook.com/me?fields=' + settings.FB_USER_FIELDS
    session_info = session.get(info_url).json()
    if session_info['email'] is None:
        raise UserAccountExistsError(session_info)
    return session_info
