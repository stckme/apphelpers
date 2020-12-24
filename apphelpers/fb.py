import os

from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix


from converge import settings


AUTORIZATION_BASE_URL= 'https://www.facebook.com/dialog/oauth'


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'True'


def create_fb_session():
    session = OAuth2Session(settings.FB_APP_ID,
                            redirect_uri=settings.FB_RETURN_URL,
                            scope=settings.FB_SCOPE)
    return facebook_compliance_fix(session)


def get_auth_url():
    # Redirect user to Facebook for authorization
    session = create_fb_session()
    authorization_url, state = session.authorization_url(AUTORIZATION_BASE_URL)
    return authorization_url


def fetch_info(access_token):
    session = OAuth2Session(token={'access_token': access_token})
    info_url = 'https://graph.facebook.com/me?fields=' + settings.FB_USER_FIELDS
    return session.get(info_url).json()
