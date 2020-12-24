import os

from requests_oauthlib import OAuth2Session


from converge import settings


AUTORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/auth"


if not settings.G_REDIRECT_URI.startswith('https'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'True'


def create_goo_session():
    session = OAuth2Session(settings.G_CLIENT_ID,
                            redirect_uri=settings.G_REDIRECT_URI,
                            scope=settings.G_SCOPE)
    return session


def get_auth_url():
    # Redirect user to Google for authorization
    session = create_goo_session()
    authorization_url, state = session.authorization_url(
        AUTORIZATION_BASE_URL, access_type='online'
    )
    return authorization_url


def fetch_info(access_token):
    session = OAuth2Session(token={'access_token': access_token})
    userinfo = session.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
    return userinfo
